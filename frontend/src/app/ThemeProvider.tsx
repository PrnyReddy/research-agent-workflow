"use client";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import React from "react";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#232326", contrastText: "#f3f3f3" },
    secondary: { main: "#444", contrastText: "#f3f3f3" },
    background: { default: "#18181b", paper: "#232326" },
    text: { primary: "#f3f3f3", secondary: "#bdbdbd" },
    divider: "#333",
    action: {
      hover: "#222",
      selected: "#333",
      disabled: "#555",
      disabledBackground: "#232326",
      active: "#111",
    },
    error: { main: "#888" },
    info: { main: "#888" },
    success: { main: "#888" },
    warning: { main: "#888" },
  },
  typography: {
    fontFamily: "Inter, Arial, sans-serif",
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 700 },
    h4: { fontWeight: 700 },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 700 },
    body1: { fontSize: "1rem" },
    body2: { fontSize: "0.9rem" },
  },
  shape: { borderRadius: 12 },
  spacing: 8,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          background: "#232326",
          color: "#f3f3f3",
          boxShadow: "0 2px 8px 0 rgba(0,0,0,0.10)",
          borderRadius: 8,
          fontWeight: 600,
          textTransform: "none",
          transition: "background 0.2s, color 0.2s, box-shadow 0.2s",
          '&:hover': {
            background: "#333",
            color: "#fff",
            boxShadow: "0 4px 16px 0 rgba(0,0,0,0.14)",
          },
          '&:active': {
            background: "#18181b",
            color: "#fff",
            boxShadow: "0 2px 8px 0 rgba(0,0,0,0.18)",
          },
          '&.Mui-disabled': {
            background: "#232326",
            color: "#555",
            boxShadow: "none",
          },
        },
        containedPrimary: {
          background: "#232326",
          color: "#f3f3f3",
        },
        containedSecondary: {
          background: "#444",
          color: "#f3f3f3",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: "#232326",
          color: "#f3f3f3",
          boxShadow: "0 4px 24px 0 rgba(0,0,0,0.10)",
          borderRadius: 16,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          background: "#232326",
          color: "#f3f3f3",
          borderRadius: 8,
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          background: "#232326",
          color: "#f3f3f3",
          '&.Mui-selected': {
            background: "#333",
            color: "#fff",
          },
          '&.Mui-selected:hover': {
            background: "#444",
            color: "#fff",
          },
          '&:hover': {
            background: "#333",
            color: "#fff",
          },
        },
      },
    },
  },
});

export default function MuiThemeProvider({ children }: { children: React.ReactNode }) {
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}