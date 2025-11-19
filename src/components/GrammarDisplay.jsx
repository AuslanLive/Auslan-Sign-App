import HighlightedText from './HighlightedText';
import grammarDict from '../ambiguous_dict_lowercase.json';
import fullWordList from '../fullWordList.json';

const GrammarDisplay = ({ grammarParsedText, alwaysShowGrammar }) => {
  if (!alwaysShowGrammar || !grammarParsedText) return null;

  return (
    <div style={{
      padding: '8px 12px',
      backgroundColor: 'rgba(0, 0, 0, 0.32)',
      border: 'none',
      borderRadius: '8px',
      fontSize: '18px',
      color: '#ffffff',
      fontFamily: "Inter, 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
      boxShadow: '0 0 0 1px rgba(190, 155, 210, 0.3), 0 0 6px rgba(190, 155, 210, 0.15)',
      flexShrink: 0
    }}>
      <div style={{
        fontSize: '16px',
        color: 'rgba(255, 255, 255, 0.6)',
        marginBottom: '4px',
        fontWeight: '500'
      }}>
        Auslan Grammar:
      </div>
      <HighlightedText
        text={grammarParsedText.charAt(0).toUpperCase() + grammarParsedText.slice(1)}
        dict={grammarDict}
        fullWordList={fullWordList}
        onWordClick={(word, value) => {
          // Optional: Add any additional logic here
        }}
      />
    </div>
  );
};

export default GrammarDisplay;
