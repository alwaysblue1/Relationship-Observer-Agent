'use client';

import { useState, useCallback } from 'react';

interface Props {
  onUpload: (file: File) => void;
  disabled: boolean;
}

export function FileUploader({ onUpload, disabled }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const handleSubmit = () => {
    if (file && !disabled) onUpload(file);
  };

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer
          ${dragOver
            ? 'border-accent-lavender bg-accent-lavender/5'
            : 'border-slate-700 hover:border-slate-500 bg-slate-800/20'
          }
        `}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".txt,.json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) setFile(f);
          }}
        />

        {file ? (
          <div>
            <div className="w-12 h-12 rounded-xl bg-slate-700 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <p className="text-sm text-slate-300">{file.name}</p>
            <p className="text-xs text-slate-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="mt-3 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              更换文件
            </button>
          </div>
        ) : (
          <div>
            <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
              </svg>
            </div>
            <p className="text-sm text-slate-400">拖拽文件到此处，或点击选择</p>
            <p className="text-xs text-slate-600 mt-2">支持 .txt / .json 格式</p>
          </div>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || disabled}
        className={`
          w-full mt-4 py-3 rounded-xl text-sm font-medium transition-all
          ${file && !disabled
            ? 'bg-gradient-to-r from-accent-lavender to-accent-rose text-white hover:opacity-90'
            : 'bg-slate-800 text-slate-600 cursor-not-allowed'
          }
        `}
      >
        开始分析
      </button>
    </div>
  );
}
