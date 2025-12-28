"use client";

import React, { useEffect, useState } from "react";

type HealthInfo = {
  fastapi?: string;
  docker?: Record<string, string>;
  obsidian_vault_exists?: boolean;
  error?: string;
};

type EnvIssue = {
  type: "docker" | "obsidian" | "backend";
  message: string;
};

export function EnvCheckBanner() {
  const [issues, setIssues] = useState<EnvIssue[]>([]);
  const [dismissed, setDismissed] = useState(false);
  const [checking, setChecking] = useState(true);

  const checkEnvironment = async () => {
    const newIssues: EnvIssue[] = [];

    try {
      // 1. Backend health check
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(3000),
      });

      if (!res.ok) {
        newIssues.push({
          type: "backend",
          message: `백엔드 서버 응답 오류 (${res.status})`,
        });
      } else {
        const data: HealthInfo = await res.json();

        // 2. Docker container check (only UDO-related containers)
        if (data.docker) {
          const udoContainers = Object.entries(data.docker)
            .filter(([name]) => name.startsWith("udo_")); // Only check udo_* containers

          const stoppedContainers = udoContainers
            .filter(([, status]) => !status.toLowerCase().startsWith("up"))
            .map(([name]) => name);

          if (stoppedContainers.length > 0) {
            newIssues.push({
              type: "docker",
              message: `Docker 컨테이너 정지됨: ${stoppedContainers.join(", ")}`,
            });
          }
        }

        // 3. Obsidian vault check
        if (data.obsidian_vault_exists === false) {
          newIssues.push({
            type: "obsidian",
            message: "Obsidian Vault를 찾을 수 없습니다. Obsidian을 실행해 주세요.",
          });
        }
      }
    } catch (error) {
      // Backend not reachable
      newIssues.push({
        type: "backend",
        message: "백엔드 서버에 연결할 수 없습니다. Docker Desktop을 실행하고 서버를 시작해 주세요.",
      });
    }

    setIssues(newIssues);
    setChecking(false);
  };

  useEffect(() => {
    checkEnvironment();

    // Re-check every 30 seconds
    const interval = setInterval(checkEnvironment, 30000);
    return () => clearInterval(interval);
  }, []);

  // Don't show if dismissed or no issues or still checking
  if (dismissed || issues.length === 0 || checking) {
    return null;
  }

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[9999] bg-yellow-400 text-yellow-900 px-4 py-3 shadow-lg animate-in slide-in-from-top duration-300"
      role="alert"
    >
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <strong className="font-semibold">환경 설정 문제 감지</strong>
            <ul className="mt-1 text-sm list-disc list-inside">
              {issues.map((issue, idx) => (
                <li key={idx}>{issue.message}</li>
              ))}
            </ul>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={checkEnvironment}
            className="px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors text-sm"
          >
            다시 확인
          </button>
          <button
            onClick={() => setDismissed(true)}
            className="px-3 py-1 bg-yellow-800 text-white rounded hover:bg-yellow-900 transition-colors text-sm"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
