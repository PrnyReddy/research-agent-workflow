"use client";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import React from "react";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#1976d2" },
    secondary: { main: "#43ea7a" },
    background: { default: "#18181b", paper: "#232326" },
    text: { primary: "#f3f3f3", secondary: "#bdbdbd" },
    error: { main: "#d32f2f" },
    info: { main: "#0288d1" },
    success: { main: "#43ea7a" },
    warning: { main: "#ffa726" },
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
});

export default function MuiThemeProvider({ children }: { children: React.ReactNode }) {
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}