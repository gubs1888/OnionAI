# Mobile tests (TEAM C)

Current smoke test process (works today, zero extra deps):

    cd mobile
    npm run smoke          # = tsc --noEmit, strict typecheck of every screen

Planned (once the flow is stable — do NOT spend day-1 time here):

    npm i -D jest jest-expo @testing-library/react-native
    # then add jest.config.js with preset "jest-expo" and write render tests:
    #   - Home renders "New Batch"
    #   - Results renders all contract fields for the mock assessment
    #   - navigation: batch -> camera -> analyzing -> results -> report

Until jest lands, this folder intentionally contains no executable test file
so `tsc --noEmit` stays the single source of truth.
