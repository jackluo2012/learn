import { NextPage } from "next";
import Footer from "../Footer";
import Navbar from "../Navbar";
import { AntdRegistry } from '@ant-design/nextjs-registry';
import '@ant-design/v5-patch-for-react-19';
interface LayoutProps {
  children: React.ReactNode;
}

const Layout: NextPage<LayoutProps> = ({ children }) => {
  return (
    <html lang="en">
      <body>
      <AntdRegistry>
      <Navbar />
      <main>{children}</main>
      <Footer />
      </AntdRegistry>
      </body>
      </html>
  );
};

export default Layout;