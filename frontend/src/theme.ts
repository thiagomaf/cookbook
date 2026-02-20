import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

/**
 * CookbookPreset — extends Aura with:
 * - Primary: teal (replaces default emerald)
 * - Surface: stone warm-gray (replaces slate in light, zinc in dark)
 * - Border radius: slightly larger (md = 10px, lg = 14px)
 */
export const CookbookPreset = definePreset(Aura, {
  primitive: {
    borderRadius: {
      none: '0',
      xs:   '4px',
      sm:   '6px',
      md:   '10px',
      lg:   '14px',
      xl:   '20px',
    },
  },
  semantic: {
    primary: {
      50:  '{teal.50}',
      100: '{teal.100}',
      200: '{teal.200}',
      300: '{teal.300}',
      400: '{teal.400}',
      500: '{teal.500}',
      600: '{teal.600}',
      700: '{teal.700}',
      800: '{teal.800}',
      900: '{teal.900}',
      950: '{teal.950}',
    },
    colorScheme: {
      light: {
        surface: {
          0:   '#ffffff',
          50:  '{stone.50}',
          100: '{stone.100}',
          200: '{stone.200}',
          300: '{stone.300}',
          400: '{stone.400}',
          500: '{stone.500}',
          600: '{stone.600}',
          700: '{stone.700}',
          800: '{stone.800}',
          900: '{stone.900}',
          950: '{stone.950}',
        },
      },
      dark: {
        surface: {
          0:   '#ffffff',
          50:  '{stone.50}',
          100: '{stone.100}',
          200: '{stone.200}',
          300: '{stone.300}',
          400: '{stone.400}',
          500: '{stone.500}',
          600: '{stone.600}',
          700: '{stone.700}',
          800: '{stone.800}',
          900: '{stone.900}',
          950: '{stone.950}',
        },
      },
    },
  },
})
