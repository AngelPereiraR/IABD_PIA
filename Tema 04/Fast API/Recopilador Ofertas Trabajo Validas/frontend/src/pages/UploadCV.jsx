import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadMasterCV } from "../api/client";
import { Upload, CheckCircle } from "lucide-react";

export function UploadCV() {
  const [file, setFile] = useState(null);
  const upload = useMutation({ mutationFn: uploadMasterCV });

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-6">📄 CV Maestro</h1>
      <p className="text-gray-600 mb-4">
        Sube tu CV base en PDF. El engine lo adaptará a cada oferta automáticamente.
      </p>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Upload className="mx-auto mb-3 text-gray-400" size={32} />
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="hidden"
          id="cv-upload"
        />
        <label htmlFor="cv-upload" className="cursor-pointer text-indigo-600 hover:underline">
          Seleccionar PDF
        </label>
        {file && <p className="mt-2 text-sm text-gray-600">{file.name}</p>}
      </div>

      {upload.isSuccess && (
        <div className="mt-4 flex items-center gap-2 text-green-700 bg-green-50 p-3 rounded">
          <CheckCircle size={18} />
          <span>CV subido correctamente</span>
          {upload.data?.master_cv_url && (
            <a href={upload.data.master_cv_url} target="_blank" rel="noopener noreferrer"
               className="ml-auto text-sm underline">Ver PDF</a>
          )}
        </div>
      )}

      {upload.isError && (
        <p className="mt-4 text-red-600 text-sm">Error: {upload.error.message}</p>
      )}

      <button
        onClick={() => file && upload.mutate(file)}
        disabled={!file || upload.isPending}
        className="mt-4 w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
      >
        {upload.isPending ? "Subiendo..." : "Subir CV Maestro"}
      </button>
    </div>
  );
}
