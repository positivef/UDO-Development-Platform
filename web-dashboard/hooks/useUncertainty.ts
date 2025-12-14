import { useQuery } from "@tanstack/react-query";
import { UncertaintyStatusResponse } from "@/types/uncertainty";
import apiClient from "@/lib/api/client";

async function fetchUncertaintyStatus(): Promise<UncertaintyStatusResponse> {
    const response = await apiClient.get<UncertaintyStatusResponse>("/api/uncertainty/status");
    return response.data;
}

export function useUncertainty() {
    return useQuery({
        queryKey: ["uncertainty-status"],
        queryFn: fetchUncertaintyStatus,
        refetchInterval: 30000, // Refresh every 30 seconds
        staleTime: 10000,
    });
}
