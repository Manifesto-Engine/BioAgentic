// @ts-check
import { themes as prismThemes } from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'BioAgentic',
  tagline: 'Cultivate autonomous, biologically-inspired AI agents.',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://www.manifesto-engine.com',
  baseUrl: '/',

  organizationName: 'Manifesto-Engine',
  projectName: 'BioAgentic',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/social-card.png',
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'BioAgentic',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'docsSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            to: '/docs/api-reference',
            label: 'API',
            position: 'left',
          },
          {
            href: 'https://github.com/Manifesto-Engine/BioAgentic',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              { label: 'Introduction', to: '/docs/intro' },
              { label: 'Quickstart', to: '/docs/quickstart' },
              { label: 'API Reference', to: '/docs/api-reference' },
            ],
          },
          {
            title: 'Resources',
            items: [
              { label: 'Sovereign Script', to: '/docs/sovereign-script' },
              { label: 'Organs', to: '/docs/organs' },
              { label: 'Advanced', to: '/docs/advanced' },
            ],
          },
          {
            title: 'Links',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/Manifesto-Engine/BioAgentic',
              },
            ],
          },
        ],
        copyright: `© ${new Date().getFullYear()} BioAgentic Collective. Sovereignty is not requested — it is declared.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'json', 'python'],
      },
    }),
};

export default config;
