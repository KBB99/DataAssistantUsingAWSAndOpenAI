import { type NextRequest, NextResponse } from 'next/server'
import { type Message } from '../../components/ChatLine'

const getUserMessage = (messages: Message[]) => {
  const lastMessage = messages[messages.length - 1]
  return lastMessage.who === 'user' ? lastMessage.message : ''
}

export const config = {
  runtime: 'edge',
}

export default async function handler(req: NextRequest) {
  // read body from request
  const body = await req.json()

  // const messages = req.body.messages
  const userMessage = getUserMessage(body.messages)
  const payload = {
    messageBody: userMessage,
    phone_number: body.phoneNumber,
  }

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const response = await fetch(process.env.API_GATEWAY_URL!, {
    headers: requestHeaders,
    method: 'POST',
    body: JSON.stringify(payload),
  })

  const data = await response.json()

  console.log(data)

  if (data.error) {
    console.error('OpenAI API error: ', data.error)
    return NextResponse.json({
      text: `ERROR with API integration. ${data.error.message}`,
    })
  }

  // return response with 200 and stringify json text
  return NextResponse.json({ text: data })
}
