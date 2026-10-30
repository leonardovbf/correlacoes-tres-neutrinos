import type { Metadata } from "next";
import "./globals.css";
import "./microbe-theme.css";

export const metadata: Metadata = {
  title: "Neutrino Lab | Laboratório de Simulações",
  description: "Comparação local de evolução exata, PSA e circuitos quânticos para neutrinos coletivos.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
