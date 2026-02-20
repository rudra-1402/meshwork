import { test, expect } from '@playwright/test'

test.describe('Authentication flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth')
  })

  test('shows email input on initial load', async ({ page }) => {
    await expect(page.getByRole('textbox', { name: /email/i })).toBeVisible()
  })

  test('login form is available for existing user flow', async ({ page }) => {
    await page.getByRole('textbox', { name: /email/i }).fill('test@student.edu')

    await expect(page.getByRole('textbox', { name: /password/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /login/i })).toBeVisible()
  })

  test('switching to signup shows extra fields', async ({ page }) => {
    await page.getByRole('button', { name: /sign up/i }).click()
    await page.getByRole('textbox', { name: /email/i }).fill(`new_${Date.now()}@student.edu`)

    await expect(page.getByLabel(/first name/i)).toBeVisible()
    await expect(page.getByLabel(/confirm password/i)).toBeVisible()
  })

  test('invalid email domain shows error', async ({ page }) => {
    await page.getByRole('textbox', { name: /email/i }).fill('someone@gmail.com')
    await page.getByRole('textbox', { name: /email/i }).blur()

    await expect(page.getByRole('alert').first()).toBeVisible()
  })
})
