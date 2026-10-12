"use client";

import { UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";


type AccountLinkProps = {
  variant?: "icon" | "menu";
  onClick?: () => void;
  className?: string;
};


export function AccountLink({
  variant = "icon",
  onClick,
  className = "",
}: AccountLinkProps) {
  const pathname =
    usePathname();

  const {
    user,
    isLoading,
  } = useAuth();


  const isAuthenticated =
    Boolean(user);


  const href =
    isAuthenticated
      ? "/account"
      : "/login?next=/account";


  const label =
    isAuthenticated
      ? "حساب کاربری"
      : "ورود / ساخت حساب";


  const isActive =
    pathname.startsWith(
      "/account",
    )
    || pathname.startsWith(
      "/login",
    );


  if (
    variant === "menu"
  ) {
    return (
      <Link
        href={href}
        onClick={() => {
          onClick?.();
        }}
        aria-label={
          isLoading
            ? "حساب کاربری"
            : label
        }
        aria-current={
          isActive
            ? "page"
            : undefined
        }
        className={`
          group
          flex
          min-h-12
          items-center
          justify-between
          gap-4
          text-sm
          font-medium
          transition-colors
          ${
            isActive
              ? "text-elasi-gold"
              : "text-elasi-text hover:text-elasi-gold"
          }
          ${className}
        `}
      >
        <span className="flex items-center gap-3">
          <span className="relative flex size-8 items-center justify-center">
            <UserRound
              size={19}
              strokeWidth={1.7}
              aria-hidden="true"
            />

            {!isLoading
            && isAuthenticated ? (
              <span
                aria-hidden="true"
                className="
                  absolute
                  right-0
                  top-0
                  size-2
                  rounded-full
                  border
                  border-elasi-ivory
                  bg-elasi-gold
                "
              />
            ) : null}
          </span>

          <span>
            {isLoading
              ? "حساب کاربری"
              : label}
          </span>
        </span>


        {!isLoading
        && isAuthenticated ? (
          <span
            className="
              rounded-full
              bg-elasi-green/[0.055]
              px-2.5
              py-1
              text-[9px]
              font-medium
              text-elasi-green
            "
          >
            وارد شده
          </span>
        ) : null}
      </Link>
    );
  }


  return (
    <Link
      href={href}
      aria-label={
        isLoading
          ? "حساب کاربری"
          : label
      }
      title={
        isLoading
          ? "حساب کاربری"
          : label
      }
      aria-current={
        isActive
          ? "page"
          : undefined
      }
      className={`
        relative
        flex
        size-10
        items-center
        justify-center
        rounded-full
        transition-colors
        ${
          isActive
            ? "bg-elasi-green/5 text-elasi-gold"
            : "text-elasi-green hover:bg-elasi-green/5 hover:text-elasi-gold"
        }
        ${className}
      `}
    >
      <UserRound
        size={20}
        strokeWidth={1.7}
        aria-hidden="true"
      />

      {!isLoading
      && isAuthenticated ? (
        <span
          aria-hidden="true"
          className="
            absolute
            -right-0.5
            -top-0.5
            size-2.5
            rounded-full
            border-2
            border-elasi-ivory
            bg-elasi-gold
          "
        />
      ) : null}
    </Link>
  );
}