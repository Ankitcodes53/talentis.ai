import React, { useEffect, useState } from "react";
import axios from "axios";

export default function RecruiterReview({ token, attemptId }) {
  const [data, setData] = useState(null);
  useEffect(()=>{
    if(!attemptId) return;
    axios.get(`/api/video-interviews/review/${attemptId}`, { headers: { Authorization: `Bearer ${token}` }}).then(r=> setData(r.data)).catch(console.error);
  },[attemptId, token]);

  if(!data) return <div>Loading...</div>;
  return (
    <div className="p-4 bg-white rounded shadow">
      <h3 className="text-lg font-semibold mb-2">Interview Review</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="font-semibold">Camera Recording</h4>
          {data.video_url ? <video src={data.video_url} controls width="100%" /> : <div>No camera recording</div>}
          <h4 className="mt-3 font-semibold">Screen Recording</h4>
          {data.screen_url ? <video src={data.screen_url} controls width="100%" /> : <div>No screen recording</div>}
        </div>
        <div>
          <h4 className="font-semibold">Transcript</h4>
          <pre className="text-xs bg-gray-50 p-2 rounded max-h-64 overflow-auto">{data.transcript || "No transcript yet"}</pre>
          <h4 className="mt-3 font-semibold">Behavior Analysis</h4>
          <pre className="text-xs bg-gray-50 p-2 rounded max-h-48 overflow-auto">{JSON.stringify(data.behavior_analysis || {}, null, 2)}</pre>
          <h4 className="mt-3 font-semibold">Proctoring Flags</h4>
          <pre className="text-xs bg-gray-50 p-2 rounded">{JSON.stringify(data.proctoring_flags || {}, null, 2)}</pre>
          <div className="mt-2">Cheating risk: {data.cheating_risk ?? "N/A"}</div>
        </div>
      </div>
    </div>
  );
}
