import DashboardClientLayout from './client-layout';

export const metadata = {
  title: 'Tekkscope | Dashboard',
  description: 'Manage and edit your Tekkscope page',
  icons: '/logos/icon.png',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function DashboardLayout({ children }) {
  return <DashboardClientLayout>{children}</DashboardClientLayout>;
}