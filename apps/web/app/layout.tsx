import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./globals.css"
import Topbar from "@/components/Topbar"
import Footer from "@/components/Footer"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "计算机职业方向雷达 | CS Job Radar",
  description:
    "基于真实招聘需求，分析 Java、Go、前端、Android、AI 应用、测试开发等方向的岗位趋势、薪资区间和技能要求。",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable}`}
    >
      <body>
        <Topbar />
        {children}
        <Footer />
      </body>
    </html>
  )
}
