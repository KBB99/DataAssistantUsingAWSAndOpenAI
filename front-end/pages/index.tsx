import { Layout, Text, Page } from '@vercel/examples-ui'
import { Chat } from '../components/Chat'

function Home() {
  return (
    <Page className="flex flex-col gap-12">
      <section className="flex flex-col gap-6">
        <Text variant="h1">GPT-3 OpenAI and AWS</Text>
        <Text className="text-zinc-600">
          In this example, a simple chat bot is implemented using Next.js, API
          Routes, OpenAI API, and AWS. Say `I want to book a flight` to see the
          implementation in action.
        </Text>
      </section>

      <section className="flex flex-col gap-3">
        <Text variant="h2">AI Assistant:</Text>
        <div className="lg:w-2/3">
          <Chat />
        </div>
      </section>
    </Page>
  )
}

Home.Layout = Layout

export default Home
