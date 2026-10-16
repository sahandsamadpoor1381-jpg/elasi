"use client";

import {
  Heart,
  X,
} from "lucide-react";

import Link from "next/link";

import { usePathname } from "next/navigation";

import {
  useEffect,
  useRef,
} from "react";

import { AccountLink } from "@/components/auth/account-link";

import {
  isNavigationItemActive,
  navigationItems,
} from "./navigation-items";


type MobileNavigationDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
};


const focusableElementsSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(",");


export function MobileNavigationDrawer({
  isOpen,
  onClose,
}: MobileNavigationDrawerProps) {
  const pathname =
    usePathname();

  const drawerRef =
    useRef<HTMLElement>(
      null,
    );

  const closeButtonRef =
    useRef<HTMLButtonElement>(
      null,
    );


  useEffect(() => {
    if (!isOpen) {
      return;
    }


    const previousOverflow =
      document.body.style.overflow;


    const previouslyFocusedElement =
      document.activeElement
        instanceof HTMLElement
        ? document.activeElement
        : null;


    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (
        event.key === "Escape"
      ) {
        onClose();

        return;
      }


      if (
        event.key !== "Tab"
      ) {
        return;
      }


      const drawer =
        drawerRef.current;


      if (!drawer) {
        return;
      }


      const focusableElements =
        Array.from(
          drawer.querySelectorAll<HTMLElement>(
            focusableElementsSelector,
          ),
        ).filter(
          (element) =>
            !element.hasAttribute(
              "disabled",
            ),
        );


      if (
        focusableElements.length
        === 0
      ) {
        event.preventDefault();

        return;
      }


      const firstFocusableElement =
        focusableElements[0];

      const lastFocusableElement =
        focusableElements[
          focusableElements.length
          - 1
        ];


      if (
        event.shiftKey
        && document.activeElement
          === firstFocusableElement
      ) {
        event.preventDefault();

        lastFocusableElement.focus();

        return;
      }


      if (
        !event.shiftKey
        && document.activeElement
          === lastFocusableElement
      ) {
        event.preventDefault();

        firstFocusableElement.focus();
      }
    }


    document.body.style.overflow =
      "hidden";


    window.addEventListener(
      "keydown",
      handleKeyDown,
    );


    const focusFrame =
      window.requestAnimationFrame(
        () => {
          closeButtonRef.current
            ?.focus();
        },
      );


    return () => {
      window.cancelAnimationFrame(
        focusFrame,
      );

      document.body.style.overflow =
        previousOverflow;

      window.removeEventListener(
        "keydown",
        handleKeyDown,
      );

      previouslyFocusedElement
        ?.focus();
    };
  }, [
    isOpen,
    onClose,
  ]);


  const drawerState =
    isOpen
      ? "open"
      : "closed";


  return (
    <div
      aria-hidden={
        !isOpen
      }
      inert={
        !isOpen
      }
      className={`
        fixed
        inset-0
        z-50
        lg:hidden
        ${
          isOpen
            ? "pointer-events-auto"
            : "pointer-events-none"
        }
      `}
    >
      <button
        type="button"
        aria-label="بستن منوی اصلی"
        onClick={
          onClose
        }
        data-state={
          drawerState
        }
        className="
          elasi-mobile-drawer-overlay
          absolute
          inset-0
          bg-black/30
        "
      />


      <aside
        ref={
          drawerRef
        }
        role="dialog"
        aria-modal="true"
        aria-label="منوی اصلی موبایل"
        data-state={
          drawerState
        }
        className="
          elasi-mobile-drawer-panel
          absolute
          inset-y-0
          right-0
          w-[min(88vw,360px)]
          bg-elasi-ivory
          shadow-2xl
        "
      >
        <div
          data-state={
            drawerState
          }
          className="
            elasi-mobile-drawer-content
            flex
            h-full
            flex-col
          "
        >
          <div
            className="
              flex
              min-h-16
              items-center
              justify-between
              border-b
              border-elasi-green/10
              px-5
            "
          >
            <Link
              href="/"
              onClick={
                onClose
              }
              aria-label="صفحه اصلی ELASI"
              className="
                text-lg
                font-semibold
                tracking-[0.18em]
                text-elasi-green
              "
            >
              ELASI
            </Link>


            <button
              ref={
                closeButtonRef
              }
              type="button"
              aria-label="بستن منو"
              onClick={
                onClose
              }
              className="
                flex
                size-11
                items-center
                justify-center
                rounded-full
                text-elasi-green
                transition-colors
                hover:bg-elasi-green/5
                hover:text-elasi-gold-text
              "
            >
              <X
                size={21}
                strokeWidth={1.7}
                aria-hidden="true"
              />
            </button>
          </div>


          <nav
            aria-label="ناوبری موبایل"
            className="
              flex-1
              overflow-y-auto
              px-5
              py-6
            "
          >
            <ul className="flex flex-col">
              {navigationItems.map(
                (item) => {
                  const isActive =
                    isNavigationItemActive(
                      pathname,
                      item.href,
                    );


                  return (
                    <li
                      key={
                        item.href
                      }
                    >
                      <Link
                        href={
                          item.href
                        }
                        onClick={
                          onClose
                        }
                        aria-current={
                          isActive
                            ? "page"
                            : undefined
                        }
                        className={`
                          relative
                          flex
                          min-h-12
                          items-center
                          border-b
                          border-elasi-green/8
                          pr-3
                          text-base
                          font-medium
                          transition-colors
                          ${
                            isActive
                              ? "text-elasi-gold-text"
                              : "text-elasi-text hover:text-elasi-gold-text"
                          }
                        `}
                      >
                        <span
                          aria-hidden="true"
                          className={`
                            absolute
                            right-0
                            h-5
                            w-px
                            bg-elasi-gold
                            transition-opacity
                            duration-200
                            ${
                              isActive
                                ? "opacity-100"
                                : "opacity-0"
                            }
                          `}
                        />

                        {item.label}
                      </Link>
                    </li>
                  );
                },
              )}
            </ul>


            <div
              className="
                mt-8
                border-t
                border-elasi-green/10
                pt-5
              "
            >
              <AccountLink
                variant="menu"
                onClick={
                  onClose
                }
              />


              <Link
                href="/wishlist"
                onClick={
                  onClose
                }
                className="
                  flex
                  min-h-12
                  items-center
                  gap-3
                  text-sm
                  font-medium
                  text-elasi-text
                  transition-colors
                  hover:text-elasi-gold-text
                "
              >
                <span
                  className="
                    flex
                    size-8
                    items-center
                    justify-center
                  "
                >
                  <Heart
                    size={19}
                    strokeWidth={1.7}
                    aria-hidden="true"
                  />
                </span>

                علاقه‌مندی‌ها
              </Link>
            </div>
          </nav>
        </div>
      </aside>
    </div>
  );
}