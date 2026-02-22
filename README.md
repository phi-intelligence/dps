This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on AWS Amplify

This app is set up for [AWS Amplify Hosting](https://console.aws.amazon.com/amplify/):

1. Open the [Amplify console](https://console.aws.amazon.com/amplify/) and choose **Create new app**.
2. Choose your **Git provider** (e.g. GitHub), then choose **Next** (framework).
3. Select the **phi-intelligence/dps** repository and the **main** branch, then **Next**.
4. Let Amplify **Create and use a new service role** (or pick an existing one), then **Next**.
5. Review and choose **Save and deploy**.

Build settings are in `amplify.yml` (Next.js SSR with `baseDirectory: .next`). Amplify will build and host the app and give you a URL.

## Deploy on Vercel

You can also deploy on the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme). See [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
