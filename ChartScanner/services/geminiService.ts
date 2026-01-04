import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { ChartEntry } from '../types';

// Pull the API key from Vite env in the browser or process.env when running under Node.
const getApiKey = (): string => {
  const keyFromVite = (import.meta as any)?.env?.VITE_API_KEY;
  const keyFromProcess = typeof process !== 'undefined' ? process.env?.VITE_API_KEY : undefined;
  const resolved = keyFromVite ?? keyFromProcess;
  if (!resolved) {
    throw new Error('Missing VITE_API_KEY. Set it in your .env file or environment.');
  }
  return resolved;
};

export const extractChartData = async (
  base64ImageData: string,
  mimeType: string,
): Promise<ChartEntry[]> => {
  const ai = new GoogleGenAI({ apiKey: getApiKey() });

  // Refined prompt to explicitly request only JSON output
  const prompt = `From the provided image of a Spotify Viral Chart, extract the top 10 songs.
  For each song, identify its rank (1-10), title, and artist name.
  Return the data strictly as a JSON array of objects, each with 'rank', 'title', and 'artist' properties.
  Ensure the ranks are sequential from 1 to 10 based on the chart order.
  Do not include any conversational text, introductory remarks, or markdown formatting outside of the JSON array itself.`;

  const imagePart = {
    inlineData: {
      mimeType: mimeType,
      data: base64ImageData,
    },
  };

  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: 'gemini-2.5-flash-image',
      contents: { parts: [imagePart, { text: prompt }] },
      // Removed responseMimeType and responseSchema as they are not supported for gemini-2.5-flash-image
      // config: {
      //   responseMimeType: "application/json",
      //   responseSchema: { ... }
      // },
    });

    let jsonStr = response.text?.trim();

    if (!jsonStr) {
      throw new Error("No text response received from the API. The model might have failed to generate content.");
    }

    // Attempt to extract JSON from a markdown code block if present
    const jsonMatch = jsonStr.match(/```json\n([\s\S]*?)\n```/);
    if (jsonMatch && jsonMatch[1]) {
      jsonStr = jsonMatch[1].trim();
    } else {
      // If no markdown block, try to clean up potential leading/trailing non-JSON text.
      // This is a heuristic and might need adjustment based on typical model output.
      // It removes anything before the first '[' or '{' and after the last ']' or '}'.
      const firstJsonChar = Math.min(jsonStr.indexOf('['), jsonStr.indexOf('{'));
      const lastJsonChar = Math.max(jsonStr.lastIndexOf(']'), jsonStr.lastIndexOf('}'));

      if (firstJsonChar !== -1 && lastJsonChar !== -1 && lastJsonChar > firstJsonChar) {
          jsonStr = jsonStr.substring(firstJsonChar, lastJsonChar + 1);
      } else {
          // If basic JSON structure not found after trimming, it's likely not JSON.
          console.warn("Raw response text did not contain expected JSON structure:", jsonStr);
      }
    }

    if (!jsonStr.startsWith('[') && !jsonStr.startsWith('{')) {
        throw new Error(`Model response could not be parsed as valid JSON. Response received: "${jsonStr.substring(0, 200)}..."`);
    }

    try {
      const parsedData: ChartEntry[] = JSON.parse(jsonStr);
      // Basic validation for the parsed data structure
      if (!Array.isArray(parsedData) || !parsedData.every(item =>
        typeof item === 'object' && item !== null &&
        typeof item.rank === 'number' && typeof item.title === 'string' && typeof item.artist === 'string'
      )) {
        throw new Error("Received invalid JSON format for chart entries. Ensure each entry has 'rank', 'title', and 'artist'.");
      }
      return parsedData;
    } catch (parseError) {
      console.error("JSON parsing error:", parseError);
      throw new Error(`Failed to parse JSON from model response. Raw text: "${jsonStr.substring(0, 200)}..."`);
    }
  } catch (error: unknown) {
    console.error("Gemini API call or processing failed:", error);
    let errorMessage = "An unexpected error occurred during chart data extraction.";
    if (error instanceof Error) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    }
    throw new Error(errorMessage);
  }
};