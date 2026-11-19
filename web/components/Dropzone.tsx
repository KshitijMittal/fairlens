"use client";

import { useState, useCallback, useRef } from "react";

interface DropzoneProps {
  onFileSelect: (file: File) => void;
  acceptedTypes?: string[];
  maxSizeMB?: number;
  disabled?: boolean;
  /** Signed out: the same surface, but it opens sign-in instead of the picker. */
  locked?: boolean;
  onLockedClick?: () => void;
  hint?: string;
}

export default function Dropzone({
  onFileSelect,
  acceptedTypes = [".csv", ".xlsx"],
  maxSizeMB = 50,
  disabled = false,
  locked = false,
  onLockedClick,
  hint,
}: DropzoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setDragActive(e.type === "dragenter" || e.type === "dragover");
    }
  }, [disabled]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (disabled) return;
    if (locked) {
      onLockedClick?.();
      return;
    }

    const file = e.dataTransfer.files[0];
    if (file) {
      validateAndSelect(file);
    }
  }, [disabled]);

  const handleClick = () => {
    if (locked) {
      onLockedClick?.();
      return;
    }
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSelect(file);
    }
    // Reset input so same file can be selected again
    e.target.value = "";
  };

  const validateAndSelect = (file: File) => {
    setError(null);

    // Check extension
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!acceptedTypes.includes(ext)) {
      setError(`Only ${acceptedTypes.join(", ")} files are supported.`);
      return;
    }

    // Check size (client-side, server enforces too)
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`File is ${(file.size / 1024 / 1024).toFixed(1)} MB. Maximum is ${maxSizeMB} MB.`);
      return;
    }

    onFileSelect(file);
  };

  const inputAccept = acceptedTypes.join(",");

  return (
    <div>
      <div
        className={`dropzone${dragActive ? " dropzone--active" : ""}`}
        onClick={handleClick}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled || undefined}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        {!locked && (
        <input
          ref={fileInputRef}
          type="file"
          accept={inputAccept}
          onChange={handleFileChange}
          aria-label="Choose a CSV or XLSX file"
          style={{ display: "none" }}
          disabled={disabled}
        />
        )}
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.25"
          aria-hidden="true"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p className="title">Drop a CSV or XLSX file here, or click to browse</p>
        <p className="hint">{hint ?? `Maximum ${maxSizeMB} MB`}</p>
      </div>
      {error && (
        <p className="notice" style={{ marginTop: 12 }}>{error}</p>
      )}
    </div>
  );
}
