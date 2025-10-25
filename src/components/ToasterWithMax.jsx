import React, { useEffect, useRef, useState } from "react";
import toast, { Toaster, useToasterStore } from 'react-hot-toast';

function useMaxToasts(max) {
  const { toasts } = useToasterStore();
  React.useEffect(() => {
    toasts
      .filter((t) => t.visible)
      .filter((_, i) => i >= max)
      .forEach((t) => toast.dismiss(t.id));
  }, [toasts, max]);
}

const ToasterWithMax = React.forwardRef((props, ref) => {
  const max = props.max || 3;
  useMaxToasts(max);
  return <Toaster {...props} />;
});


export default ToasterWithMax;
