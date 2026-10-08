"use client";

import { useState } from "react";
import { SceneViewer } from "@/components/viewer/SceneViewer";
import { UploadCloud, CheckCircle2, Loader2 } from "lucide-react";
import axios from "axios";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "processing" | "completed" | "error">("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus("uploading");
    
    // In a real flow, you'd use FormData to send the file.
    // We'll simulate it for the mock.
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Assuming backend runs on 8000
      const res = await axios.post("http://localhost:8000/api/reconstruct", formData);
      const { job_id } = res.data;
      setJobId(job_id);
      setStatus("processing");
      
      // Simulate polling
      setTimeout(async () => {
        const metadataRes = await axios.get(`http://localhost:8000/api/result/${job_id}/metadata`);
        setMetadata(metadataRes.data.metadata);
        
        const modelRes = await axios.get(`http://localhost:8000/api/result/${job_id}/model`);
        
        // For the mock, we can set the model URL to a simple sample or leave it null 
        // to show the placeholder in the viewer if the sample doesn't exist.
        // We will pass the mock url, but our viewer handles non-existent gracefully.
        setModelUrl(modelRes.data.model_url);
        setStatus("completed");
      }, 2000);
    } catch (error) {
      console.error(error);
      setStatus("error");
    }
  };

  return (
    <main className="min-h-screen bg-black text-white p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        <header className="border-b border-neutral-800 pb-4">
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            FLOORPLAN <span className="text-orange-500">→</span> 3D
          </h1>
          <p className="text-neutral-400 text-sm mt-1">Metric-aware floorplan reconstruction</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[80vh]">
          
          {/* Left Column: Upload & Stats */}
          <div className="lg:col-span-1 space-y-6 flex flex-col">
            
            {/* Upload Area */}
            <div className="border-2 border-dashed border-neutral-800 rounded-xl p-8 flex flex-col items-center justify-center text-center space-y-4 bg-neutral-900/50 flex-shrink-0 transition-colors hover:border-orange-500/50">
              <div className="p-4 bg-neutral-800 rounded-full text-orange-500">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div>
                <p className="font-medium">Upload Floor Plan</p>
                <p className="text-sm text-neutral-500 mt-1">Drag & drop or browse</p>
              </div>
              <input 
                type="file" 
                className="text-sm text-neutral-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-500 file:text-black hover:file:bg-orange-400 cursor-pointer" 
                accept="image/*"
                onChange={handleFileChange}
              />
              <button 
                onClick={handleUpload}
                disabled={!file || status === "uploading" || status === "processing"}
                className="w-full mt-4 bg-orange-500 text-black font-semibold py-2 rounded hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {status === "uploading" ? "Uploading..." : status === "processing" ? "Processing..." : "Reconstruct"}
              </button>
            </div>

            {/* Status */}
            {status !== "idle" && (
              <div className="p-4 rounded-xl border border-neutral-800 bg-neutral-900/50 flex items-center gap-3">
                {status === "processing" || status === "uploading" ? (
                  <Loader2 className="w-5 h-5 text-orange-500 animate-spin" />
                ) : status === "completed" ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : null}
                <div className="text-sm">
                  <p className="font-medium text-neutral-200 capitalize">{status}</p>
                  {jobId && <p className="text-neutral-500 font-mono text-xs">Job ID: {jobId.slice(0, 8)}</p>}
                </div>
              </div>
            )}

            {/* Stats */}
            <div className="border border-neutral-800 rounded-xl bg-neutral-900/50 flex-grow p-6">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-500 mb-4">Reconstruction Stats</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-neutral-800/50 rounded-lg">
                  <p className="text-xs text-neutral-400 uppercase tracking-wider">Rooms</p>
                  <p className="text-2xl font-light">{metadata?.rooms ?? "--"}</p>
                </div>
                <div className="p-3 bg-neutral-800/50 rounded-lg">
                  <p className="text-xs text-neutral-400 uppercase tracking-wider">Walls</p>
                  <p className="text-2xl font-light">{metadata?.walls ?? "--"}</p>
                </div>
                <div className="p-3 bg-neutral-800/50 rounded-lg">
                  <p className="text-xs text-neutral-400 uppercase tracking-wider">Doors</p>
                  <p className="text-2xl font-light">{metadata?.doors ?? "--"}</p>
                </div>
                <div className="p-3 bg-neutral-800/50 rounded-lg">
                  <p className="text-xs text-neutral-400 uppercase tracking-wider">Windows</p>
                  <p className="text-2xl font-light">{metadata?.windows ?? "--"}</p>
                </div>
                <div className="col-span-2 p-3 bg-neutral-800/50 rounded-lg border border-orange-500/20">
                  <p className="text-xs text-orange-500/80 uppercase tracking-wider font-semibold">Scale (mm/px)</p>
                  <p className="text-2xl font-light text-orange-50">{metadata?.scale_mm_per_px ?? "--"}</p>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: 3D Viewer */}
          <div className="lg:col-span-2 relative min-h-[400px]">
            <SceneViewer modelUrl={modelUrl} />
          </div>

        </div>
      </div>
    </main>
  );
}
