import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  KeyRound,
  DatabaseZap,
  CreditCard,
  Settings,
  FlaskConical
} from 'lucide-react';
import { SidebarMenu } from '@/components/ui/sidebar';
import { useCallback } from 'react';

export function SidebarLinks() {
  const pathname = usePathname();
  const isActive = useCallback((path) => path === pathname, [pathname]);

  const menuItemBaseClass =
    'flex items-center w-full px-4 py-2.5 rounded-md transition-all duration-200 ease-in-out text-sm';
  const menuItemActiveClass = 'bg-tekk-bg /50 text-white/80 font-medium';
  const menuItemInactiveClass = 'text-gray-300';

  return (
    <SidebarMenu className="space-y-2 px-2 text-gray-700">
      {/*========== Dashboard ============*/}
      <Link
        href="/dashboard"
        passHref
        className={`${menuItemBaseClass} ${
          isActive('/dashboard') ? menuItemActiveClass : menuItemInactiveClass
        }`}
      >
        <Home className="mr-3 h-5 w-5" />
        <span>Dashboard</span>
      </Link>

      {/*========== Playground ============*/}
      <Link
        href="/dashboard/playground"
        passHref
        className={`${menuItemBaseClass} ${
          isActive('/dashboard/playground')
            ? menuItemActiveClass
            : menuItemInactiveClass
        }`}
      >
        <FlaskConical className="mr-3 h-5 w-5" />
        <span>Playground</span>
      </Link>

      {/*========== API Keys ============*/}
      <Link
        href="/dashboard/api-keys"
        passHref
        className={`${menuItemBaseClass} ${
          isActive('/dashboard/api-keys')
            ? menuItemActiveClass
            : menuItemInactiveClass
        }`}
      >
        <KeyRound className="mr-3 h-5 w-5" />
        <span>API Keys</span>
      </Link>

      {/*========== Usage ============*/}
      <Link
        href="/dashboard/usage"
        passHref
        className={`${menuItemBaseClass} ${
          isActive('/dashboard/usage')
            ? menuItemActiveClass
            : menuItemInactiveClass
        }`}
      >
        <DatabaseZap className="mr-3 h-5 w-5" />
        <span>Usage</span>
      </Link>

      {/*========== Billings ============*/}
      <Link
        href="/dashboard/billing"
        passHref
        className={`${menuItemBaseClass} ${
          isActive('/dashboard/billing')
            ? menuItemActiveClass
            : menuItemInactiveClass
        }`}
      >
        <CreditCard className="mr-3 h-5 w-5" />
        <span>Billings</span>
      </Link>

      {/*========== Settings ============*/}
      <Link
        href="/dashboard/settings"
        passHref
        className={`${menuItemBaseClass} ${
          isActive('/dashboard/settings')
            ? menuItemActiveClass
            : menuItemInactiveClass
        }`}
      >
        <Settings className="mr-3 h-5 w-5" />
        <span>Settings</span>
      </Link>
    </SidebarMenu>
  );
}
