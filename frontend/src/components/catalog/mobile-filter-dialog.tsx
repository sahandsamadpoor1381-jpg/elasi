"use client";

import {
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";
import { SlidersHorizontal, X } from "lucide-react";

import { formatNumber } from "@/lib/format";


type MobileFilterDialogProps = {
  activeFilterCount: number;
  children: ReactNode;
};


export function MobileFilterDialog({
  activeFilterCount,
  children,
}: MobileFilterDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [isOpen, setIsOpen] = useState(false);

  function openDialog() {
    const dialog = dialogRef.current;

    if (dialog && !dialog.open) {
      dialog.showModal();
      setIsOpen(true);
    }
  }

  function closeDialog() {
    const dialog = dialogRef.current;

    if (dialog?.open) {
      dialog.close();
    }

    setIsOpen(false);
    triggerRef.current?.focus();
  }

  function handleBackdropClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === event.currentTarget) {
      closeDialog();
    }
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="dialog"
        aria-controls="catalog-filter-dialog"
        aria-expanded={isOpen}
        onClick={openDialog}
        className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-elasi-border-strong bg-white px-5 text-sm font-semibold text-elasi-green transition-colors hover:border-elasi-gold-text hover:bg-elasi-green/[0.03] focus-visible:outline-offset-2"
      >
        <SlidersHorizontal size={18} aria-hidden="true" />
        <span>فیلتر و مرتب‌سازی</span>
        {activeFilterCount > 0 ? (
          <span className="inline-flex min-w-6 items-center justify-center rounded-full bg-elasi-green px-1.5 text-xs leading-6 text-elasi-white">
            {formatNumber(activeFilterCount)}
          </span>
        ) : null}
      </button>

      <dialog
        ref={dialogRef}
        id="catalog-filter-dialog"
        aria-labelledby="catalog-filter-dialog-title"
        aria-modal="true"
        onClose={() => {
          setIsOpen(false);
          triggerRef.current?.focus();
        }}
        onCancel={() => setIsOpen(false)}
        onClick={handleBackdropClick}
        className="fixed inset-0 m-0 h-dvh w-full max-h-none max-w-none border-0 bg-transparent p-0 text-elasi-text backdrop:bg-elasi-green/40"
      >
        <div className="absolute inset-x-0 bottom-0 flex max-h-[var(--filter-panel-max-height)] flex-col overflow-hidden rounded-t-card border border-elasi-green/10 bg-elasi-ivory shadow-[var(--shadow-medium)] sm:inset-y-0 sm:my-auto sm:max-h-[var(--filter-panel-max-height)] sm:w-full sm:max-w-xl sm:rounded-card">
          <div className="flex shrink-0 items-center justify-between gap-4 border-b border-elasi-green/10 px-5 py-4">
            <h2
              id="catalog-filter-dialog-title"
              className="text-lg font-semibold text-elasi-green"
            >
              فیلتر محصولات
            </h2>

            <button
              type="button"
              onClick={closeDialog}
              aria-label="بستن فیلترها"
              className="inline-flex size-11 shrink-0 items-center justify-center rounded-full border border-elasi-border-strong bg-white text-elasi-green transition-colors hover:border-elasi-gold-text hover:bg-elasi-green/[0.04] focus-visible:outline-offset-2"
            >
              <X size={20} aria-hidden="true" />
            </button>
          </div>

          {children}
        </div>
      </dialog>
    </>
  );
}
