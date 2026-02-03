import GovernanceDashboard from "@/components/governance/governance-dashboard";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Governance - UDO Platform",
  description: "Project governance rules, templates, and compliance dashboard",
};

export default function GovernancePage() {
  return <GovernanceDashboard />;
}
