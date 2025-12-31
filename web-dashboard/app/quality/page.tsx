"use client"

import { QualityMetrics } from "@/components/dashboard/quality-metrics"
import { motion } from "framer-motion"
import { ArrowLeft, Code2 } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

export default function QualityPage() {
  const t = useTranslations()

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="p-6 space-y-6">
        {/* Navigation */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('common.back')} {t('navigation.dashboard')}
          </Link>
        </motion.div>

        {/* Page Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-blue-500/10">
              <Code2 className="h-8 w-8 text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">{t('quality.title')}</h1>
              <p className="text-gray-400 mt-1">
                {t('quality.description')}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Quality Metrics Component */}
        <QualityMetrics apiUrl="http://localhost:8000/api/quality-metrics" />

        {/* Info Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <h2 className="text-xl font-bold text-white mb-4">{t('quality.scoreBreakdown')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="p-4 rounded-lg bg-gray-700/30">
              <h3 className="font-semibold text-blue-400 mb-2">Python (Pylint)</h3>
              <p className="text-gray-400">
                {t('quality.pylintDesc')}
                {t('quality.weight')}: <span className="text-white font-medium">30%</span>
              </p>
            </div>
            <div className="p-4 rounded-lg bg-gray-700/30">
              <h3 className="font-semibold text-purple-400 mb-2">TypeScript (ESLint)</h3>
              <p className="text-gray-400">
                {t('quality.eslintDesc')}
                {t('quality.weight')}: <span className="text-white font-medium">30%</span>
              </p>
            </div>
            <div className="p-4 rounded-lg bg-gray-700/30">
              <h3 className="font-semibold text-green-400 mb-2">{t('quality.testCoverage')}</h3>
              <p className="text-gray-400">
                {t('quality.coverageDesc')}
                {t('quality.weight')}: <span className="text-white font-medium">40%</span>
              </p>
            </div>
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <h2 className="text-xl font-bold text-white mb-4">{t('quality.quickActions')}</h2>
          <div className="flex flex-wrap gap-3">
            <button className="px-4 py-2 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors">
              {t('quality.runPylint')}
            </button>
            <button className="px-4 py-2 rounded-lg bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-colors">
              {t('quality.runEslint')}
            </button>
            <button className="px-4 py-2 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors">
              {t('quality.runTests')}
            </button>
            <button className="px-4 py-2 rounded-lg bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20 transition-colors">
              {t('quality.viewReport')}
            </button>
          </div>
        </motion.div>
      </div>
    </main>
  )
}
