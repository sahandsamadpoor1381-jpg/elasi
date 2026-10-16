"use client";

import {
  Check,
  ChevronDown,
  Search,
} from "lucide-react";

import {
  type KeyboardEvent,
  useMemo,
  useState,
} from "react";


export type LocationOption = {
  value: string;
  label: string;
};


type LocationSelectProps = {
  id: string;
  label: string;

  value: string;

  options: LocationOption[];

  placeholder: string;

  onChange: (
    value: string,
  ) => void;

  disabled?: boolean;

  error?: string;

  searchable?: boolean;
};


export function LocationSelect({
  id,
  label,
  value,
  options,
  placeholder,
  onChange,
  disabled = false,
  error,
  searchable = false,
}: LocationSelectProps) {
  const [
    isOpen,
    setIsOpen,
  ] =
    useState(false);


  const [
    query,
    setQuery,
  ] =
    useState("");


  const selectedOption =
    options.find(
      (option) =>
        option.value ===
        value,
    );


  const filteredOptions =
    useMemo(
      () => {
        const normalizedQuery =
          query.trim();


        if (!normalizedQuery) {
          return options;
        }


        return options.filter(
          (option) =>
            option.label.includes(
              normalizedQuery,
            ),
        );
      },
      [
        options,
        query,
      ],
    );


  const listboxId =
    `${id}-listbox`;


  const errorId =
    `${id}-error`;


  function closeDropdown() {
    setIsOpen(false);

    setQuery("");
  }


  function handleSelect(
    option: LocationOption,
  ) {
    onChange(
      option.value,
    );

    closeDropdown();
  }


  function handleToggle() {
    if (disabled) {
      return;
    }


    setIsOpen(
      (current) =>
        !current,
    );


    setQuery("");
  }


  function handleTriggerKeyDown(
    event:
      KeyboardEvent<HTMLButtonElement>,
  ) {
    if (
      event.key ===
      "Escape"
    ) {
      event.preventDefault();

      closeDropdown();

      return;
    }


    if (
      event.key ===
        "Enter" ||
      event.key ===
        " "
    ) {
      event.preventDefault();

      handleToggle();

      return;
    }


    if (
      event.key ===
      "ArrowDown"
    ) {
      event.preventDefault();

      if (!isOpen) {
        setIsOpen(true);
      }
    }
  }


  function handleDropdownKeyDown(
    event:
      KeyboardEvent<HTMLDivElement>,
  ) {
    if (
      event.key ===
      "Escape"
    ) {
      event.preventDefault();

      closeDropdown();
    }
  }


  return (
    <div className="relative">
      <label
        htmlFor={id}
        className="mb-2 block text-sm font-medium text-elasi-text"
      >
        {label}

        <span
          aria-hidden="true"
          className="mr-1 text-elasi-gold"
        >
          *
        </span>
      </label>


      <button
        id={id}
        type="button"
        disabled={
          disabled
        }
        aria-haspopup="listbox"
        aria-expanded={
          isOpen
        }
        aria-controls={
          isOpen
            ? listboxId
            : undefined
        }
        aria-describedby={
          error
            ? errorId
            : undefined
        }
        onClick={
          handleToggle
        }
        onKeyDown={
          handleTriggerKeyDown
        }
        className={[
          "flex",
          "min-h-14",
          "w-full",
          "items-center",
          "justify-between",
          "gap-4",
          "rounded-[16px]",
          "border",
          "px-4",
          "text-right",
          "text-sm",
          "outline-none",
          "transition-all",
          "duration-200",

          error
            ? "border-red-300 bg-red-50/30"
            : "border-elasi-green/15 bg-elasi-ivory/50",

          disabled
            ? "cursor-not-allowed opacity-45"
            : "cursor-pointer hover:border-elasi-gold/50 hover:bg-white",

          isOpen
            ? "border-elasi-gold bg-white ring-4 ring-elasi-gold/10"
            : "",
        ].join(" ")}
      >
        <span
          className={
            selectedOption
              ? "font-medium text-elasi-green"
              : "text-elasi-muted"
          }
        >
          {selectedOption
            ? selectedOption.label
            : placeholder}
        </span>


        <ChevronDown
          size={18}
          strokeWidth={1.6}
          aria-hidden="true"
          className={[
            "shrink-0",
            "text-elasi-muted",
            "transition-transform",
            "duration-200",

            isOpen
              ? "rotate-180 text-elasi-gold"
              : "",
          ].join(" ")}
        />
      </button>


      {error ? (
        <p
          id={errorId}
          className="mt-2 text-xs text-red-700"
        >
          {error}
        </p>
      ) : null}


      {isOpen &&
      !disabled ? (
        <>
          <button
            type="button"
            tabIndex={-1}
            aria-hidden="true"
            onClick={
              closeDropdown
            }
            className="fixed inset-0 z-40 cursor-default"
          />


          <div
            onKeyDown={
              handleDropdownKeyDown
            }
            className="
              absolute
              right-0
              top-[calc(100%+10px)]
              z-50
              w-full
              overflow-hidden
              rounded-[20px]
              border
              border-elasi-green/10
              bg-white
              shadow-[0_22px_60px_rgba(21,42,36,0.14)]
            "
          >
            {searchable ? (
              <div className="border-b border-elasi-green/10 bg-white p-3">
                <div
                  className="
                    flex
                    items-center
                    gap-3
                    rounded-[14px]
                    border
                    border-elasi-green/10
                    bg-elasi-ivory/70
                    px-3
                    transition-all
                    duration-200
                    focus-within:border-elasi-gold
                    focus-within:bg-white
                    focus-within:ring-4
                    focus-within:ring-elasi-gold/10
                  "
                >
                  <Search
                    size={17}
                    strokeWidth={1.6}
                    className="shrink-0 text-elasi-muted"
                    aria-hidden="true"
                  />


                  <input
                    type="text"
                    role="searchbox"
                    inputMode="search"
                    value={
                      query
                    }
                    autoFocus
                    onChange={(
                      event,
                    ) =>
                      setQuery(
                        event.target.value,
                      )
                    }
                    placeholder="جست‌وجوی شهر..."
                    className="
                      min-h-11
                      w-full
                      appearance-none
                      border-0
                      bg-transparent
                      text-sm
                      text-elasi-text
                      outline-none
                      ring-0
                      shadow-none
                      placeholder:text-elasi-muted/65
                      focus:border-0
                      focus:outline-none
                      focus:ring-0
                      focus:shadow-none
                      focus-visible:outline-none
                      focus-visible:ring-0
                      focus-visible:shadow-none
                    "
                    style={{
                      outline: "none",
                      boxShadow:
                        "none",
                    }}
                  />
                </div>
              </div>
            ) : null}


            <div
              id={
                listboxId
              }
              role="listbox"
              aria-label={
                label
              }
              className="
                max-h-[min(320px,45vh)]
                overflow-y-auto
                overscroll-contain
                bg-white
                p-2
              "
            >
              {filteredOptions.length >
              0 ? (
                filteredOptions.map(
                  (
                    option,
                  ) => {
                    const isSelected =
                      option.value ===
                      value;


                    return (
                      <button
                        key={
                          option.value
                        }
                        type="button"
                        role="option"
                        aria-selected={
                          isSelected
                        }
                        onClick={() =>
                          handleSelect(
                            option,
                          )
                        }
                        className={[
                          "mb-1",
                          "flex",
                          "min-h-11",
                          "w-full",
                          "items-center",
                          "justify-between",
                          "gap-4",
                          "rounded-[12px]",
                          "border",
                          "px-3",
                          "text-right",
                          "text-sm",
                          "transition-all",
                          "duration-150",

                          isSelected
                            ? "border-elasi-gold/25 bg-elasi-gold/10 font-medium text-elasi-green"
                            : "border-transparent bg-transparent text-elasi-text hover:bg-elasi-ivory hover:text-elasi-green",
                        ].join(
                          " ",
                        )}
                      >
                        <span
                          style={{
                            color:
                              isSelected
                                ? "var(--elasi-green)"
                                : undefined,
                          }}
                        >
                          {
                            option.label
                          }
                        </span>


                        {isSelected ? (
                          <Check
                            size={16}
                            strokeWidth={2}
                            aria-hidden="true"
                            style={{
                              color:
                                "var(--elasi-gold)",
                            }}
                          />
                        ) : null}
                      </button>
                    );
                  },
                )
              ) : (
                <div className="px-4 py-8 text-center text-sm text-elasi-muted">
                  نتیجه‌ای پیدا نشد.
                </div>
              )}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}