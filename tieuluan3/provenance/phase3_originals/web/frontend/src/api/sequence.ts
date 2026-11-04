export function parseSequenceText(text: string, expectedRows: number): number[][] {
  const rows = text
    .trim()
    .split(/\r?\n/)
    .map((row) => row.trim())
    .filter(Boolean);

  if (rows.length !== expectedRows) {
    throw new Error(`Sequence phải có đúng ${expectedRows} hàng dữ liệu.`);
  }

  return rows.map((row, index) => {
    const values = row.split(",").map((value) => Number(value.trim()));
    if (values.length !== 5 || values.some((value) => !Number.isFinite(value))) {
      throw new Error(`Hàng ${index + 1} phải có đúng 5 số hữu hạn.`);
    }
    return values;
  });
}


export function formatSequence(sequence: number[][]): string {
  return sequence.map((row) => row.join(", ")).join("\n");
}
