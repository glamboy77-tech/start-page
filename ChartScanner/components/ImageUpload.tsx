import React from 'react';

interface ImageUploadProps {
  previewUrl: string | null;
  onFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({ previewUrl, onFileChange }) => {
  return (
    <div className="w-full mb-6 p-4 border-2 border-dashed border-gray-300 rounded-lg text-center bg-gray-50">
      <label htmlFor="file-upload" className="cursor-pointer">
        {previewUrl ? (
          <img
            src={previewUrl}
            alt="Chart Preview"
            className="max-w-full h-auto mx-auto rounded-md shadow-sm mb-4"
            style={{ maxHeight: '300px', objectFit: 'contain' }}
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-gray-500">
            <svg
              className="w-12 h-12 mb-3 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              ></path>
            </svg>
            <p className="text-lg font-medium">Click to upload an image of a Spotify Viral Chart</p>
            <p className="text-sm text-gray-400 mt-1">PNG, JPG, JPEG (Max 5MB)</p>
          </div>
        )}
        <input
          id="file-upload"
          type="file"
          accept="image/png, image/jpeg, image/jpg"
          onChange={onFileChange}
          className="hidden"
        />
      </label>
      {previewUrl && (
        <p className="mt-4 text-sm text-gray-600">Image selected. Ready for extraction.</p>
      )}
    </div>
  );
};
