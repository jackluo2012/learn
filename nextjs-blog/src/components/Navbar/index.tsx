'use client'
import {useState} from "react";
import Link from "next/link";
import { navs } from "./config";
import styles from "./index.module.scss";
import { Button, Menu } from 'antd';
import Login from "../Login";
const Navbar = () => {
  const [isShowLogin, setIsShowLogin] = useState(false);
  const handleGotoEditorPage= () => {
  };
  const handleClose = () => {
    setIsShowLogin(false);
  };
  const HandleLogin = ()=> {
    setIsShowLogin(true);
  };

  return (
    <div className={styles.navbar}>
      <section className={styles.logoArea}>BLOG-C</section>
      <section className={styles.linkArea}>
        <Menu 
          mode="horizontal" 
          items={navs?.map((nav, index) => ({
            key: index,
            label: (
              <Link href={nav.path}>
                {nav.name}
              </Link>
            ),
          }))} 
          className={styles.customMenu} // 应用新的自定义类名
        />
      </section>
      <section className={styles.operationArea}>
      <Button onClick={handleGotoEditorPage}>写文章</Button>
      <Button type="primary" onClick={HandleLogin}>登录</Button>
      </section>
      <Login isShow={isShowLogin} onClose= {handleClose}/>
    </div>
  );
}

export default Navbar;