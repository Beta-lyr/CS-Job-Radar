import Link from "next/link"

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div>© 2026 计算机职业方向雷达 · 面向学生的技术岗位数据观察</div>
        <div className="footer-links">
          <Link href="/data-methodology">数据说明</Link>
          <a href="#">反馈建议</a>
          <a href="#">隐私政策</a>
        </div>
      </div>
    </footer>
  )
}
