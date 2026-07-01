import Link from "next/link"

export default function Topbar() {
  return (
    <header className="topbar">
      <div className="container nav">
        <Link href="/" className="brand">
          <div className="brand-symbol">JR</div>
          <div className="brand-copy">
            <strong>计算机职业方向雷达</strong>
            <span>CS Career Direction Radar</span>
          </div>
        </Link>

        <nav className="nav-links" aria-label="主导航">
          <a href="/#directions">方向观察</a>
          <a href="/#skills">技能要求</a>
          <a href="/#reports">周度报告</a>
          <a href="/#projects">项目建议</a>
          <a href="/data-methodology">数据方法</a>
        </nav>

        <a className="nav-action" href="/#reports">查看本周报告</a>
        <button className="menu-button" aria-label="打开菜单">☰</button>
      </div>
    </header>
  )
}
