"use client";
import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebar } from "@/context/SidebarContext";
import {
  GridIcon,
  CalenderIcon,
  ChevronDownIcon,
  HorizontaLDots,
  ListIcon,
  PageIcon,
  UserCircleIcon,
  PlugInIcon,
  TableIcon,
} from "@/icons/index";
import { useAuth } from "@/stores/auth-store";
import { useIsSuperAdmin, useCanManageTeam, useCanManageTerminals } from "@/lib/hooks";

type NavItem = {
  name: string;
  icon: React.ReactNode;
  path?: string;
  subItems?: { name: string; path: string; pro?: boolean; new?: boolean }[];
};

const AppSidebar: React.FC = () => {
  const { isExpanded, isMobileOpen, isHovered, setIsHovered } = useSidebar();
  const pathname = usePathname();
  const { user } = useAuth();
  const isSuperAdmin = useIsSuperAdmin();
  const canManageTerminals = useCanManageTerminals();
  const canManageTeam = useCanManageTeam();

  const tenantNav: NavItem[] = [
    { icon: <GridIcon className="w-6 h-6" />, name: "Dashboard", path: "/dashboard" },
    { icon: <ListIcon className="w-6 h-6" />, name: "Slots", path: "/slots" },
    { icon: <TableIcon className="w-6 h-6" />, name: "Analytics", path: "/analytics" },
    { icon: <PageIcon className="w-6 h-6" />, name: "Reports", path: "/reports" },
  ];

  const managementNav: NavItem[] = [];
  if (canManageTerminals) {
    managementNav.push({ icon: <PlugInIcon className="w-6 h-6" />, name: "Terminals", path: "/terminals" });
  }
  if (canManageTeam) {
    managementNav.push({ icon: <UserCircleIcon className="w-6 h-6" />, name: "Team", path: "/team" });
  }

  const adminNav: NavItem[] = [
    { icon: <GridIcon className="w-6 h-6" />, name: "Dashboard", path: "/admin/dashboard" },
    { icon: <ListIcon className="w-6 h-6" />, name: "Tenants", path: "/admin/tenants" },
    { icon: <TableIcon className="w-6 h-6" />, name: "Plans", path: "/admin/plans" },
    { icon: <PlugInIcon className="w-6 h-6" />, name: "AI Providers", path: "/admin/ai-providers" },
    { icon: <UserCircleIcon className="w-6 h-6" />, name: "Users", path: "/admin/users" },
    { icon: <CalenderIcon className="w-6 h-6" />, name: "Audit Log", path: "/admin/audit-log" },
    { icon: <PageIcon className="w-6 h-6" />, name: "Health", path: "/admin/health" },
    { icon: <PageIcon className="w-6 h-6" />, name: "Settings", path: "/admin/settings" },
  ];

  const settingsNav: NavItem[] = [
    { icon: <PlugInIcon className="w-6 h-6" />, name: "Settings", path: "/settings" },
  ];

  const profileNav: NavItem[] = [
    { icon: <UserCircleIcon className="w-6 h-6" />, name: "Profile", path: "/profile" },
  ];

  const mainNav = isSuperAdmin ? adminNav : tenantNav;

  const [openSubmenu, setOpenSubmenu] = useState<{
    type: string;
    index: number;
  } | null>(null);
  const [subMenuHeight, setSubMenuHeight] = useState<Record<string, number>>({});
  const subMenuRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const isActive = useCallback((path: string) => path === pathname, [pathname]);

  useEffect(() => {
    let submenuMatched = false;
    const allNavGroups: { items: NavItem[]; type: string }[] = [
      { items: mainNav, type: "main" },
      { items: managementNav, type: "management" },
      { items: settingsNav, type: "settings" },
      { items: profileNav, type: "profile" },
    ];

    allNavGroups.forEach(({ items, type }) => {
      items.forEach((nav, index) => {
        if (nav.subItems) {
          nav.subItems.forEach((subItem) => {
            if (isActive(subItem.path)) {
              setOpenSubmenu({ type, index });
              submenuMatched = true;
            }
          });
        }
      });
    });
    if (!submenuMatched) {
      setOpenSubmenu(null);
    }
  }, [pathname, isActive]);

  useEffect(() => {
    if (openSubmenu !== null) {
      const key = `${openSubmenu.type}-${openSubmenu.index}`;
      if (subMenuRefs.current[key]) {
        setSubMenuHeight((prevHeights) => ({
          ...prevHeights,
          [key]: subMenuRefs.current[key]?.scrollHeight || 0,
        }));
      }
    }
  }, [openSubmenu]);

  const handleSubmenuToggle = (index: number, menuType: string) => {
    setOpenSubmenu((prevOpenSubmenu) => {
      if (prevOpenSubmenu && prevOpenSubmenu.type === menuType && prevOpenSubmenu.index === index) {
        return null;
      }
      return { type: menuType, index };
    });
  };

  const renderMenuItems = (navItems: NavItem[], menuType: string) => (
    <ul className="flex flex-col gap-4">
      {navItems.map((nav, index) => (
        <li key={nav.name}>
          {nav.subItems ? (
            <button
              onClick={() => handleSubmenuToggle(index, menuType)}
              className={`menu-item group ${openSubmenu?.type === menuType && openSubmenu?.index === index ? "menu-item-active" : "menu-item-inactive"} cursor-pointer ${!isExpanded && !isHovered ? "lg:justify-center" : "lg:justify-start"}`}
            >
              <span className={`${openSubmenu?.type === menuType && openSubmenu?.index === index ? "menu-item-icon-active" : "menu-item-icon-inactive"}`}>
                {nav.icon}
              </span>
              {(isExpanded || isHovered || isMobileOpen) && (
                <span className="menu-item-text">{nav.name}</span>
              )}
              {(isExpanded || isHovered || isMobileOpen) && (
                <ChevronDownIcon
                  className={`ml-auto w-5 h-5 transition-transform duration-200 ${openSubmenu?.type === menuType && openSubmenu?.index === index ? "rotate-180 text-brand-500" : ""}`}
                />
              )}
            </button>
          ) : (
            nav.path && (
              <Link
                href={nav.path}
                className={`menu-item group ${isActive(nav.path) ? "menu-item-active" : "menu-item-inactive"}`}
              >
                <span className={`${isActive(nav.path) ? "menu-item-icon-active" : "menu-item-icon-inactive"}`}>
                  {nav.icon}
                </span>
                {(isExpanded || isHovered || isMobileOpen) && (
                  <span className="menu-item-text">{nav.name}</span>
                )}
              </Link>
            )
          )}
          {nav.subItems && (isExpanded || isHovered || isMobileOpen) && (
            <div
              ref={(el) => { subMenuRefs.current[`${menuType}-${index}`] = el; }}
              className="overflow-hidden transition-all duration-300"
              style={{
                height: openSubmenu?.type === menuType && openSubmenu?.index === index
                  ? `${subMenuHeight[`${menuType}-${index}`]}px`
                  : "0px",
              }}
            >
              <ul className="mt-2 space-y-1 ml-9">
                {nav.subItems.map((subItem) => (
                  <li key={subItem.name}>
                    <Link
                      href={subItem.path}
                      className={`menu-dropdown-item ${isActive(subItem.path) ? "menu-dropdown-item-active" : "menu-dropdown-item-inactive"}`}
                    >
                      {subItem.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </li>
      ))}
    </ul>
  );

  return (
    <aside
      className={`fixed flex flex-col top-0 px-5 left-0 bg-white dark:bg-gray-900 dark:border-gray-800 text-gray-900 h-screen transition-all duration-300 ease-in-out z-50 border-r border-gray-200 ${
        isExpanded || isMobileOpen ? "w-[290px]" : isHovered ? "w-[290px]" : "w-[90px]"
      } ${isMobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      onMouseEnter={() => !isExpanded && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={`py-6 flex shrink-0 ${!isExpanded && !isHovered ? "lg:justify-center" : "justify-start"}`}>
        <Link href="/" className="flex items-center">
          {isExpanded || isHovered || isMobileOpen ? (
            <img src="/mutell-logo.svg" alt="Mutell" className="h-32 max-w-full w-auto dark:invert" />
          ) : (
            <img src="/mutell-logo.svg" alt="Mutell" className="h-24 w-auto dark:invert" />
          )}
        </Link>
      </div>
      <div className="flex flex-col overflow-y-auto duration-300 ease-linear no-scrollbar">
        <nav className="mb-6">
          <div className="flex flex-col gap-4">
            <div>
              <h2 className={`mb-4 text-xs uppercase flex leading-[20px] text-gray-400 ${!isExpanded && !isHovered ? "lg:justify-center" : "justify-start"}`}>
                {isExpanded || isHovered || isMobileOpen ? "Menu" : <HorizontaLDots className="w-6 h-6" />}
              </h2>
              {renderMenuItems(mainNav, "main")}
            </div>

            {!isSuperAdmin && managementNav.length > 0 && (
              <div>
                <h2 className={`mb-4 text-xs uppercase flex leading-[20px] text-gray-400 ${!isExpanded && !isHovered ? "lg:justify-center" : "justify-start"}`}>
                  {isExpanded || isHovered || isMobileOpen ? "Management" : <HorizontaLDots className="w-6 h-6" />}
                </h2>
                {renderMenuItems(managementNav, "management")}
              </div>
            )}

            {!isSuperAdmin && (
              <div>
                <h2 className={`mb-4 text-xs uppercase flex leading-[20px] text-gray-400 ${!isExpanded && !isHovered ? "lg:justify-center" : "justify-start"}`}>
                  {isExpanded || isHovered || isMobileOpen ? "Account" : <HorizontaLDots className="w-6 h-6" />}
                </h2>
                {renderMenuItems(settingsNav, "settings")}
                <div className="mt-1">
                  {renderMenuItems(profileNav, "profile")}
                </div>
              </div>
            )}
          </div>
        </nav>
      </div>
    </aside>
  );
};

export default AppSidebar;
