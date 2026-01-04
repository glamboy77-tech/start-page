import { spawn } from 'child_process';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load env in order: .env.local, then .env (matches Vite convention)
dotenv.config({ path: path.resolve(__dirname, '..', '.env.local') });
dotenv.config({ path: path.resolve(__dirname, '..', '.env') });

const PYTHON_BIN = process.env.PYTHON_BIN || 'python';
const pythonScript = path.resolve(__dirname, '..', 'chart_scraper.py');
// Store outputs in homepage/data so the UI can consume them directly
const outputDir = path.resolve(__dirname, '..', '..', 'homepage', 'data');

const chartOutputs = [
  'shazam_viral_korea.png',
  'shazam_viral_global.png',
  'youtube_shorts_korea.png',
  'youtube_shorts_global.png',
].map((name) => path.join(outputDir, name));

const prompt = `From the provided image of a Spotify Viral Chart, extract the top 10 songs.
For each song, identify its rank (1-10), title, and artist name.
Return the data strictly as a JSON array of objects, each with 'rank', 'title', and 'artist' properties.
Ensure the ranks are sequential from 1 to 10 based on the chart order.
Do not include any conversational text, introductory remarks, or markdown formatting outside of the JSON array itself.`;

const getApiKey = () => {
  const apiKey = process.env.VITE_API_KEY;
  if (!apiKey) {
    throw new Error('VITE_API_KEY is not set. Add it to your environment or .env file.');
  }
  return apiKey;
};

const runPythonScraper = () => new Promise((resolve, reject) => {
  const proc = spawn(PYTHON_BIN, [pythonScript], { stdio: 'inherit' });
  proc.on('close', (code) => {
    if (code === 0) {
      resolve();
    } else {
      reject(new Error(`chart_scraper.py exited with code ${code}`));
    }
  });
  proc.on('error', (err) => reject(err));
});

const extractChartData = async (base64ImageData, mimeType) => {
  const ai = new GoogleGenAI({ apiKey: getApiKey() });

  const imagePart = {
    inlineData: {
      mimeType,
      data: base64ImageData,
    },
  };

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: { parts: [imagePart, { text: prompt }] },
  });

  let jsonStr = response.text?.trim();
  if (!jsonStr) {
    throw new Error('Model did not return text output.');
  }

  const jsonMatch = jsonStr.match(/```json\n([\s\S]*?)\n```/);
  if (jsonMatch && jsonMatch[1]) {
    jsonStr = jsonMatch[1].trim();
  } else {
    const firstJsonChar = Math.min(jsonStr.indexOf('['), jsonStr.indexOf('{'));
    const lastJsonChar = Math.max(jsonStr.lastIndexOf(']'), jsonStr.lastIndexOf('}'));
    if (firstJsonChar !== -1 && lastJsonChar !== -1 && lastJsonChar > firstJsonChar) {
      jsonStr = jsonStr.substring(firstJsonChar, lastJsonChar + 1);
    }
  }

  const parsed = JSON.parse(jsonStr);
  if (!Array.isArray(parsed)) {
    throw new Error('Parsed response is not an array.');
  }
  return parsed;
};

const saveJson = async (imagePath, data) => {
  const { name, dir } = path.parse(imagePath);
  const key = name.replace(/-/g, '_');
  const jsonData = { [key]: data };
  const jsonPath = path.join(dir, `${name}.json`);
  await fs.writeFile(jsonPath, `${JSON.stringify(jsonData, null, 2)}\n`, 'utf8');
  return jsonPath;
};

const processOneImage = async (imagePath) => {
  const base64 = await fs.readFile(imagePath, { encoding: 'base64' });

  let lastError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const chartData = await extractChartData(base64, 'image/png');
      const jsonPath = await saveJson(imagePath, chartData);
      console.log(`✔ Saved JSON: ${jsonPath}`);
      return;
    } catch (err) {
      lastError = err;
      console.warn(`Attempt ${attempt} failed for ${path.basename(imagePath)}:`, err?.message || err);
      if (attempt < 3) {
        const delayMs = 1500 * attempt;
        await new Promise((r) => setTimeout(r, delayMs));
      }
    }
  }

  throw lastError;
};

const main = async () => {
  await fs.mkdir(outputDir, { recursive: true });
  console.log('Running Python scraper...');
  await runPythonScraper();
  console.log('Python scraper finished. Processing images...');

  for (const imageName of chartOutputs) {
    const imagePath = path.resolve(__dirname, '..', imageName);
    try {
      await processOneImage(imagePath);
    } catch (err) {
      console.error(`✖ Failed on ${imageName}:`, err);
    }
  }
};

main().catch((err) => {
  console.error('Pipeline failed:', err);
  process.exit(1);
});
