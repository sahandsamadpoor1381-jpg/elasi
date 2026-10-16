"use client";

import {
  type ChangeEvent,
  type TextareaHTMLAttributes,
  useCallback,
  useEffect,
  useRef,
} from "react";


type AutoGrowTextareaProps =
  TextareaHTMLAttributes<HTMLTextAreaElement> & {
    minHeight?: number;
    maxHeight?: number;
  };


export function AutoGrowTextarea({
  minHeight = 112,
  maxHeight = 320,
  onChange,
  style,
  value,
  ...props
}: AutoGrowTextareaProps) {
  const textareaRef =
    useRef<HTMLTextAreaElement>(
      null,
    );


  const resizeTextarea =
    useCallback(
      (
        element?:
          HTMLTextAreaElement,
      ) => {
        const textarea =
          element ??
          textareaRef.current;


        if (!textarea) {
          return;
        }


        textarea.style.height =
          "auto";


        const scrollHeight =
          textarea.scrollHeight;


        const nextHeight =
          Math.min(
            Math.max(
              scrollHeight,
              minHeight,
            ),
            maxHeight,
          );


        textarea.style.height =
          `${nextHeight}px`;


        textarea.style.overflowY =
          scrollHeight >
          maxHeight
            ? "auto"
            : "hidden";
      },
      [
        maxHeight,
        minHeight,
      ],
    );


  useEffect(() => {
    resizeTextarea();
  }, [
    resizeTextarea,
    value,
  ]);


  function handleChange(
    event:
      ChangeEvent<HTMLTextAreaElement>,
  ) {
    resizeTextarea(
      event.currentTarget,
    );


    onChange?.(
      event,
    );
  }


  return (
    <textarea
      {...props}
      ref={
        textareaRef
      }
      value={
        value
      }
      rows={1}
      onChange={
        handleChange
      }
      style={{
        ...style,

        minHeight:
          `${minHeight}px`,

        maxHeight:
          `${maxHeight}px`,

        resize:
          "none",
      }}
    />
  );
}