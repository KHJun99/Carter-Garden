import Hangul from 'hangul-js';

export const applyVirtualKeyboardInput = (currentValue, key) => {
  const safeValue = currentValue ?? '';

  if (key === 'Backspace') {
    const disassembled = Hangul.disassemble(safeValue);
    if (disassembled.length === 0) return '';
    disassembled.pop();
    return Hangul.assemble(disassembled);
  }

  const isJamoKey = (Hangul.isJamo && Hangul.isJamo(key))
    || (Hangul.isConsonant && Hangul.isConsonant(key))
    || (Hangul.isVowel && Hangul.isVowel(key));

  if (isJamoKey) {
    const disassembled = Hangul.disassemble(safeValue);
    disassembled.push(key);
    return Hangul.assemble(disassembled);
  }

  return safeValue + key;
};
