"use client";

import NetworkAnimation from "@/components/common/NetworkAnimation";
import ThemeTogglerTwo from "@/components/common/ThemeTogglerTwo";
import React, { useEffect } from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    const loadGoogleScript = () => {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    };

    if (!(window as any).google) {
      loadGoogleScript();
    }
  }, []);

  return (
    <div className="relative p-6 bg-white z-1 dark:bg-gray-900 sm:p-0">
      <div className="relative flex lg:flex-row w-full h-screen justify-center flex-col dark:bg-gray-900 sm:p-0">
        {children}
        <div className="lg:w-1/2 w-full h-full hidden lg:block">
          <NetworkAnimation />
        </div>
        <div className="fixed bottom-6 right-6 z-50 hidden sm:block">
          <ThemeTogglerTwo />
        </div>
      </div>
    </div>
  );
}
