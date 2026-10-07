import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiClient, formatErrorDetail } from '../client'

describe('formatErrorDetail (Q6.3)', () => {
  it('passes a message through', () => {
    expect(formatErrorDetail('ToDo not found')).toBe('ToDo not found')
  })

  it('names the field and drops the "Value error, " prefix', () => {
    expect(
      formatErrorDetail([
        { type: 'value_error', loc: ['body', 'done'], msg: 'Value error, must not be null', input: null },
      ])
    ).toBe('done: must not be null')
  })

  it('does not repeat a field the message already names', () => {
    expect(
      formatErrorDetail([
        {
          type: 'value_error',
          loc: ['body', 'title'],
          msg: 'Value error, title must not contain control characters',
          input: 'a\tb',
        },
      ])
    ).toBe('title must not contain control characters')
  })

  it('never shows the rejected input', () => {
    const message = formatErrorDetail([
      { type: 'string_type', loc: ['body', 'title'], msg: 'Input should be a valid string', input: 'secret-value' },
    ])

    expect(message).toBe('title: Input should be a valid string')
    expect(message).not.toContain('secret-value')
  })

  it('joins several problems and keeps locations outside the body', () => {
    expect(
      formatErrorDetail([
        { type: 'less_than_equal', loc: ['query', 'limit'], msg: 'Input should be less than or equal to 100' },
        { type: 'missing', loc: ['body'], msg: 'Field required' },
      ])
    ).toBe('query.limit: Input should be less than or equal to 100; Field required')
  })

  it('gives nothing for an empty or unknown detail', () => {
    expect(formatErrorDetail('')).toBeUndefined()
    expect(formatErrorDetail([])).toBeUndefined()
    expect(formatErrorDetail(undefined)).toBeUndefined()
  })
})

describe('apiClient error messages', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const respond = (status: number, body: unknown) =>
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(body), {
          status,
          statusText: 'Error',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    )

  it('turns a 422 into a readable message, not [object Object]', async () => {
    respond(422, {
      detail: [
        {
          type: 'value_error',
          loc: ['body', 'title'],
          msg: 'Value error, title must be at most 255 characters',
          input: 'x'.repeat(300),
        },
      ],
    })

    await expect(apiClient.post('/todo', { title: 'x'.repeat(300) })).rejects.toThrow(
      'API Error 422: title must be at most 255 characters'
    )
  })

  it('keeps a message detail', async () => {
    respond(404, { detail: 'ToDo not found' })

    await expect(apiClient.get('/todo/x')).rejects.toThrow('API Error 404: ToDo not found')
  })
})
