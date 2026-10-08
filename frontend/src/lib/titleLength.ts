/**
 * Title length as the API counts it (Q6.2): in Unicode code points, after
 * stripping. String.length counts UTF-16 code units, so an emoji would
 * count twice.
 */
export const MAX_TITLE_LENGTH = 255

export const codePointLength = (value: string): number => [...value].length
