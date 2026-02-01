import { useState, useCallback } from "react";

/**
 * CryptoIcon — composant d'icône crypto avec fallback multi-niveaux.
 *
 * Sources (par ordre de priorité) :
 *   1. URL fournie via `src` (API primaire)
 *   2. CDN CoinGecko (images populaires)
 *   3. CDN CryptoCompare
 *   4. Icône générique textuelle (cercle avec symbole)
 *
 * Props :
 *   - symbol   : string (ex: "BTC", "ETH")
 *   - src      : string | null (URL primaire)
 *   - size     : number (en px, défaut 32)
 *   - className: string (classes CSS additionnelles)
 */

// Mapping des IDs CoinGecko pour les icônes les plus courantes
const COINGECKO_IDS = {
  BTC: 1, ETH: 279, SOL: 4128, BNB: 825, XRP: 44,
  ADA: 975, DOGE: 5, DOT: 12171, AVAX: 12559, LINK: 877,
  MATIC: 4713, LTC: 2, SHIB: 11939, UNI: 12504, ATOM: 1481,
  FIL: 5426, NEAR: 10365, TRX: 1094, XLM: 100, ETC: 1321
};

function getCoinGeckoUrl(symbol, size) {
  const id = COINGECKO_IDS[symbol.toUpperCase()];
  if (!id) return null;
  const sizeKey = size <= 32 ? "small" : "large";
  return `https://coin-images.coingecko.com/coins/images/${id}/${sizeKey}/${symbol.toLowerCase()}.png`;
}

function getCryptoCompareUrl(symbol) {
  return `https://www.cryptocompare.com/media/37746238/${symbol.toLowerCase()}.png`;
}

export default function CryptoIcon({ symbol = "", src = null, size = 32, className = "" }) {
  const [fallbackLevel, setFallbackLevel] = useState(0);

  const handleError = useCallback(() => {
    setFallbackLevel((prev) => prev + 1);
  }, []);

  const sym = symbol.toUpperCase();
  const sizeStyle = { width: size, height: size, minWidth: size };

  // Determine current source based on fallback level
  let currentSrc = null;
  if (fallbackLevel === 0 && src) {
    currentSrc = src;
  } else if (fallbackLevel <= 1) {
    currentSrc = getCoinGeckoUrl(sym, size);
  } else if (fallbackLevel <= 2) {
    currentSrc = getCryptoCompareUrl(sym);
  }

  // Final fallback: text icon
  if (!currentSrc || fallbackLevel > 2) {
    return (
      <div
        className={`rounded-full flex items-center justify-center bg-primary/20 text-primary font-bold ${className}`}
        style={sizeStyle}
        title={sym}
      >
        <span style={{ fontSize: size * 0.4 }}>{sym.slice(0, 3)}</span>
      </div>
    );
  }

  return (
    <img
      src={currentSrc}
      alt={sym}
      className={`rounded-full ${className}`}
      style={sizeStyle}
      onError={handleError}
    />
  );
}
