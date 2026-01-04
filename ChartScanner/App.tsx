import React, { useState, useCallback } from 'react';
import { extractChartData } from './services/geminiService';
import { ChartEntry } from './types';
import { ImageUpload } from './components/ImageUpload';
import { ChartResult } from './components/ChartResult';
import { LoadingSpinner } from './components/LoadingSpinner';

const App: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [chartData, setChartData] = useState<ChartEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setChartData(null);
      setError(null);
      // 파일명 저장 (확장자 제외)
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
      setFileName(nameWithoutExt);
    } else {
      setSelectedFile(null);
      setPreviewUrl(null);
      setError('Please select an image file.');
      setFileName(null);
    }
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!selectedFile) {
      setError('Please upload an image first.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setChartData(null);

    const reader = new FileReader();
    reader.onloadend = async () => {
      try {
        const base64Data = (reader.result as string).split(',')[1];
        const mimeType = selectedFile.type;
        const result = await extractChartData(base64Data, mimeType);
        setChartData(result);
      } catch (e: unknown) {
        let errorMessage = 'An unknown error occurred.';
        if (e instanceof Error) {
          errorMessage = e.message;
        } else if (typeof e === 'string') {
          errorMessage = e;
        }
        setError(`Failed to extract chart data: ${errorMessage}`);
        console.error('Error extracting chart data:', e);
      } finally {
        setIsLoading(false);
      }
    };
    reader.onerror = () => {
      setError('Failed to read the image file.');
      setIsLoading(false);
    };
    reader.readAsDataURL(selectedFile);
  }, [selectedFile]);

  return (
    <div className="w-full max-w-2xl bg-white p-8 rounded-lg shadow-xl flex flex-col items-center">
      <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">
        Spotify Viral Chart Extractor
      </h1>

      <ImageUpload
        previewUrl={previewUrl}
        onFileChange={handleFileChange}
      />

      <div className="mt-6 w-full">
        {error && (
          <p className="text-red-600 bg-red-100 p-3 rounded-md mb-4 text-center">{error}</p>
        )}

        <button
          onClick={handleSubmit}
          disabled={!selectedFile || isLoading}
          className={`w-full py-3 px-6 rounded-lg text-lg font-semibold transition-colors duration-300
            ${!selectedFile || isLoading
              ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
              : 'bg-green-500 hover:bg-green-600 text-white shadow-md'
            }`}
        >
          {isLoading ? 'Processing...' : 'Extract Chart Data'}
        </button>
      </div>

      {isLoading && (
        <div className="mt-8 flex flex-col items-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-600">Extracting information from the image. This might take a moment...</p>
        </div>
      )}

      {chartData && !isLoading && (
        <div className="mt-8 w-full max-h-96 overflow-y-auto border border-gray-200 rounded-lg bg-gray-50 p-4">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Extracted Chart Data (JSON)</h2>
          <ChartResult data={chartData} />
          
          <button
            onClick={() => {
              if (chartData && fileName) {
                const jsonKey = fileName.replace(/-/g, '_');
                const jsonData = { [jsonKey]: chartData };
                const jsonString = JSON.stringify(jsonData, null, 2);
                const blob = new Blob([jsonString], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `${fileName}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
              }
            }}
            className="mt-4 w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold transition-colors"
          >
            Download JSON
          </button>
        </div>
      )}
    </div>
  );
};

export default App;