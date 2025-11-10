import React from 'react';
import { styles } from '../styles/TranslateStyles';

const SwapControls = ({ 
  onSwap, 
  onTranslate, 
  animationState, 
  loading, 
  isMobile 
}) => {
  return (
    <div style={{...styles.buttons, ...(isMobile ? styles.buttonsMobileTag : {})}}>
      <button 
        onClick={onSwap} 
        style={{
          ...styles.swapButton,
          transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
        }} 
        className={`swap-button ${animationState.isAnimating ? 'swap-button-animation' : ''} ${animationState.swapButtonRepositioning ? 'swap-button-reposition' : ''}`}
      >
        <div style={styles.buttonContent}>
          <span style={styles.swapIcon} className={animationState.isAnimating ? 'swap-icon-animation' : ''}>⇄</span>
        </div>
      </button>
      
      {animationState.showTranslateButton && (
        <button
          onClick={onTranslate}
          style={{
            ...styles.translateButton,
            opacity: loading ? 0.6 : 1,
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
          className={`translate-button ${animationState.translateButtonAnimation}`}
        >
          <div style={styles.buttonContent}>
            <span style={styles.translateIcon}>✨</span>
            {loading ? 'Translate' : 'Translate'}
          </div>
        </button>
      )}
    </div>
  );
};

export default SwapControls;
