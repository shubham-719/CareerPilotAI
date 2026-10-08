import { useEffect, useState } from "react"

type Message = {
  id?: number
  role: "user" | "assistant"
  content: string
  agent_name?: string | null
  created_at?: string
}

type ChatSession = {
  id: number
  title: string
  status: string
  message_count: number
  created_at: string
}

type User = {
  id: number
  name: string
  email: string
  created_at?: string
}

type ApiResponse = {
  status: string
  session_id?: number
  intent?: string
  agent?: string
  response?: string
  message?: string
  access_token?: string
  user?: User
}

const API_BASE_URL = "http://127.0.0.1:5000/api"

function App() {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem("careerpilot_token")
  )

  const [user, setUser] = useState<User | null>(null)

  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] =
    useState<number | null>(null)

  const [messages, setMessages] = useState<Message[]>([])

  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] =
    useState(false)

  const [error, setError] = useState("")

  const [activeAgent, setActiveAgent] =
    useState("Career Agent")

  const [activeIntent, setActiveIntent] =
    useState("career")

  // =====================================================
  // AUTH HEADER
  // =====================================================

  const getAuthHeaders = () => {
    if (!token) {
      return {}
    }

    return {
      Authorization: `Bearer ${token}`,
    }
  }

  // =====================================================
  // LOAD CURRENT USER
  // =====================================================

  const loadCurrentUser = async () => {
    if (!token) {
      return
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/me`,
        {
          headers: {
            ...getAuthHeaders(),
          },
        }
      )

      const data: ApiResponse =
        await response.json()

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Authentication failed."
        )
      }

      setUser(data.user || null)
    } catch (err) {
      console.error(err)

      localStorage.removeItem(
        "careerpilot_token"
      )

      setToken(null)
      setUser(null)
    }
  }

  // =====================================================
  // LOAD CHAT SESSIONS
  // =====================================================

  const loadSessions = async () => {
    if (!token) {
      return
    }

    try {
      setError("")

      const response = await fetch(
        `${API_BASE_URL}/agent/sessions`,
        {
          headers: {
            ...getAuthHeaders(),
          },
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Failed to load chat history."
        )
      }

      setSessions(data.sessions || [])
    } catch (err) {
      console.error(err)

      setError(
        "Unable to load chat history."
      )
    }
  }

  // =====================================================
  // LOAD SINGLE CHAT
  // =====================================================

  const loadSession = async (
    sessionId: number
  ) => {
    if (!token) {
      return
    }

    try {
      setHistoryLoading(true)
      setError("")

      const response = await fetch(
        `${API_BASE_URL}/agent/sessions/${sessionId}`,
        {
          headers: {
            ...getAuthHeaders(),
          },
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Failed to load chat."
        )
      }

      const session = data.session

      const loadedMessages: Message[] =
        (session.messages || []).map(
          (message: Message) => ({
            id: message.id,
            role: message.role,
            content: message.content,
            agent_name: message.agent_name,
            created_at: message.created_at,
          })
        )

      setMessages(loadedMessages)
      setCurrentSessionId(session.id)

      const lastAssistantMessage =
        [...loadedMessages]
          .reverse()
          .find(
            (message) =>
              message.role === "assistant"
          )

      if (
        lastAssistantMessage?.agent_name
      ) {
        setActiveAgent(
          lastAssistantMessage.agent_name
        )
      }
    } catch (err) {
      console.error(err)

      setError(
        "Unable to load this conversation."
      )
    } finally {
      setHistoryLoading(false)
    }
  }

  // =====================================================
  // NEW CHAT
  // =====================================================

  const startNewChat = () => {
    setCurrentSessionId(null)
    setMessages([])
    setInput("")
    setError("")
    setActiveAgent("Career Agent")
    setActiveIntent("career")
  }

  // =====================================================
  // DELETE CHAT
  // =====================================================

  const deleteSession = async (
    sessionId: number
  ) => {
    if (!token) {
      return
    }

    const confirmed = window.confirm(
      "Delete this conversation?"
    )

    if (!confirmed) {
      return
    }

    try {
      setError("")

      const response = await fetch(
        `${API_BASE_URL}/agent/sessions/${sessionId}`,
        {
          method: "DELETE",
          headers: {
            ...getAuthHeaders(),
          },
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Failed to delete conversation."
        )
      }

      setSessions((previous) =>
        previous.filter(
          (session) =>
            session.id !== sessionId
        )
      )

      if (currentSessionId === sessionId) {
        startNewChat()
      }
    } catch (err) {
      console.error(err)

      setError(
        "Unable to delete this conversation."
      )
    }
  }

  // =====================================================
  // SEND MESSAGE
  // =====================================================

  const sendMessage = async (
    messageOverride?: string
  ) => {
    if (!token) {
      setError(
        "Please login before starting a chat."
      )
      return
    }

    const messageText =
      messageOverride ?? input

    const trimmedMessage =
      messageText.trim()

    if (!trimmedMessage || loading) {
      return
    }

    setError("")
    setInput("")

    const userMessage: Message = {
      role: "user",
      content: trimmedMessage,
    }

    setMessages((previous) => [
      ...previous,
      userMessage,
    ])

    setLoading(true)

    try {
      const response = await fetch(
        `${API_BASE_URL}/agent/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
            ...getAuthHeaders(),
          },
          body: JSON.stringify({
            message: trimmedMessage,
            ...(currentSessionId
              ? {
                  session_id:
                    currentSessionId,
                }
              : {}),
          }),
        }
      )

      const data: ApiResponse =
        await response.json()

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Failed to generate AI response."
        )
      }

      if (data.status !== "success") {
        throw new Error(
          data.message ||
            "AI request failed."
        )
      }

      if (data.session_id) {
        setCurrentSessionId(
          data.session_id
        )
      }

      if (data.agent) {
        setActiveAgent(data.agent)
      }

      if (data.intent) {
        setActiveIntent(data.intent)
      }

      const assistantMessage: Message = {
        role: "assistant",
        content:
          data.response ||
          "No response received from AI.",
        agent_name:
          data.agent || "Career Agent",
      }

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ])

      await loadSessions()
    } catch (err) {
      console.error(err)

      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      )

      setMessages((previous) =>
        previous.slice(
          0,
          Math.max(previous.length - 1, 0)
        )
      )
    } finally {
      setLoading(false)
    }
  }

  // =====================================================
  // QUICK ACTION
  // =====================================================

  const handleQuickAction = (
    prompt: string
  ) => {
    sendMessage(prompt)
  }

  // =====================================================
  // LOGOUT
  // =====================================================

  const logout = () => {
    localStorage.removeItem(
      "careerpilot_token"
    )

    setToken(null)
    setUser(null)
    setSessions([])
    setMessages([])
    setCurrentSessionId(null)
    setInput("")
    setError("")
  }

  // =====================================================
  // INITIAL AUTH LOAD
  // =====================================================

  useEffect(() => {
    if (!token) {
      return
    }

    loadCurrentUser()
    loadSessions()
  }, [token])

  // =====================================================
  // ENTER KEY
  // =====================================================

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault()
      sendMessage()
    }
  }

  // =====================================================
  // LOGIN SCREEN
  // =====================================================

  if (!token) {
    return (
      <div className="min-h-screen bg-[#020617] text-slate-100">
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />

          <div className="absolute right-0 top-1/4 h-96 w-96 rounded-full bg-violet-500/10 blur-3xl" />

          <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
        </div>

        <div className="relative flex min-h-screen items-center justify-center px-4">
          <div className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-950/70 p-8 shadow-2xl backdrop-blur-xl">
            <div className="mb-8 text-center">
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-600 text-lg font-black shadow-lg shadow-cyan-500/20">
                CP
              </div>

              <h1 className="text-2xl font-black">
                CareerPilot AI
              </h1>

              <p className="mt-2 text-sm text-slate-500">
                Sign in to access your
                personal AI career workspace.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-xs font-medium text-slate-400">
                  Email
                </label>

                <input
                  id="login-email"
                  type="email"
                  placeholder="Enter your email"
                  className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-400/40"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium text-slate-400">
                  Password
                </label>

                <input
                  id="login-password"
                  type="password"
                  placeholder="Enter your password"
                  className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-400/40"
                />
              </div>

              {error && (
                <div className="rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              <button
                onClick={async () => {
                  const emailInput =
                    document.getElementById(
                      "login-email"
                    ) as HTMLInputElement

                  const passwordInput =
                    document.getElementById(
                      "login-password"
                    ) as HTMLInputElement

                  const email =
                    emailInput.value.trim()

                  const password =
                    passwordInput.value

                  if (!email || !password) {
                    setError(
                      "Email and password are required."
                    )
                    return
                  }

                  try {
                    setError("")

                    const response =
                      await fetch(
                        `${API_BASE_URL}/auth/login`,
                        {
                          method: "POST",
                          headers: {
                            "Content-Type":
                              "application/json",
                          },
                          body: JSON.stringify({
                            email,
                            password,
                          }),
                        }
                      )

                    const data: ApiResponse =
                      await response.json()

                    if (!response.ok) {
                      throw new Error(
                        data.message ||
                          "Login failed."
                      )
                    }

                    if (
                      !data.access_token
                    ) {
                      throw new Error(
                        "Login succeeded but no access token was returned."
                      )
                    }

                    localStorage.setItem(
                      "careerpilot_token",
                      data.access_token
                    )

                    setToken(
                      data.access_token
                    )

                    setUser(
                      data.user || null
                    )
                  } catch (err) {
                    console.error(err)

                    setError(
                      err instanceof Error
                        ? err.message
                        : "Login failed."
                    )
                  }
                }}
                className="w-full rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-3 text-sm font-bold transition hover:scale-[1.01]"
              >
                Sign In
              </button>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-center text-xs text-slate-500">
                Use the account you registered
                through the backend API.
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // =====================================================
  // MAIN APPLICATION
  // =====================================================

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100">
      {/* =================================================
          BACKGROUND
      ================================================= */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />

        <div className="absolute right-0 top-1/4 h-96 w-96 rounded-full bg-violet-500/10 blur-3xl" />

        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
      </div>

      <div className="relative flex min-h-screen">
        {/* =================================================
            SIDEBAR
        ================================================= */}

        <aside className="hidden w-72 shrink-0 border-r border-white/10 bg-slate-950/70 backdrop-blur-xl lg:flex lg:flex-col">
          <div className="border-b border-white/10 p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-600 text-sm font-black">
                CP
              </div>

              <div>
                <h1 className="font-bold">
                  CareerPilot AI
                </h1>

                <p className="text-xs text-slate-500">
                  Autonomous Career Agent
                </p>
              </div>
            </div>
          </div>

          <div className="p-4">
            <button
              onClick={startNewChat}
              className="w-full rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-3 text-sm font-semibold shadow-lg shadow-cyan-500/10 transition hover:scale-[1.01]"
            >
              + New Chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-3 pb-4">
            <div className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Recent Chats
            </div>

            {sessions.length === 0 ? (
              <div className="rounded-xl border border-dashed border-white/10 p-4 text-center text-xs text-slate-500">
                No conversations yet.
              </div>
            ) : (
              <div className="space-y-1">
                {sessions.map(
                  (session) => (
                    <div
                      key={session.id}
                      className={`group flex items-center gap-2 rounded-xl border px-2 py-2 ${
                        currentSessionId ===
                        session.id
                          ? "border-cyan-400/20 bg-cyan-400/10"
                          : "border-transparent hover:border-white/10 hover:bg-white/5"
                      }`}
                    >
                      <button
                        onClick={() =>
                          loadSession(
                            session.id
                          )
                        }
                        className="min-w-0 flex-1 text-left"
                      >
                        <div className="truncate text-sm font-medium text-slate-200">
                          {session.title}
                        </div>

                        <div className="mt-1 text-[11px] text-slate-500">
                          {session.message_count}{" "}
                          messages
                        </div>
                      </button>

                      <button
                        onClick={() =>
                          deleteSession(
                            session.id
                          )
                        }
                        className="rounded-lg px-2 py-1 text-xs text-slate-600 opacity-0 hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
                      >
                        ×
                      </button>
                    </div>
                  )
                )}
              </div>
            )}
          </div>

          <div className="border-t border-white/10 p-4">
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-violet-600 text-xs font-bold">
                  {user?.name
                    ?.charAt(0)
                    .toUpperCase() || "U"}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold">
                    {user?.name || "User"}
                  </div>

                  <div className="truncate text-[11px] text-slate-500">
                    {user?.email || ""}
                  </div>
                </div>
              </div>

              <button
                onClick={logout}
                className="mt-3 w-full rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-400 transition hover:border-red-400/20 hover:bg-red-400/5 hover:text-red-400"
              >
                Sign Out
              </button>
            </div>
          </div>
        </aside>

        {/* =================================================
            MAIN
        ================================================= */}

        <main className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/70 px-4 py-4 backdrop-blur-xl sm:px-6 lg:px-8">
            <div className="mx-auto flex max-w-7xl items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-violet-600 text-xs font-black lg:hidden">
                  CP
                </div>

                <div>
                  <h2 className="text-sm font-semibold sm:text-base">
                    {currentSessionId
                      ? "CareerPilot Conversation"
                      : "CareerPilot AI"}
                  </h2>

                  <div className="mt-1 flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                    <span className="text-xs text-slate-500">
                      {activeAgent}
                    </span>
                  </div>
                </div>
              </div>

              <div className="hidden items-center gap-3 sm:flex">
                <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-400">
                  {user?.name || "Authenticated User"}
                </div>

                <div className="rounded-full border border-emerald-400/20 bg-emerald-400/5 px-3 py-1.5 text-xs text-emerald-400">
                  ● Secure
                </div>
              </div>
            </div>
          </header>

          {/* =================================================
              CHAT
          ================================================= */}

          <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-5xl">
              {historyLoading && (
                <div className="mb-6 flex justify-center">
                  <div className="rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-2 text-xs text-cyan-300">
                    Loading conversation...
                  </div>
                </div>
              )}

              {error && (
                <div className="mb-6 rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              {messages.length === 0 && (
                <div className="flex min-h-[65vh] flex-col items-center justify-center text-center">
                  <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-cyan-400/20 via-blue-500/20 to-violet-600/20 ring-1 ring-white/10">
                    <div className="text-3xl">
                      ✦
                    </div>
                  </div>

                  <p className="mb-3 text-sm font-medium text-cyan-400">
                    YOUR AUTONOMOUS CAREER AGENT
                  </p>

                  <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl">
                    Build your career
                    <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-violet-400 bg-clip-text text-transparent">
                      {" "}smarter.
                    </span>
                  </h1>

                  <p className="mx-auto mt-5 max-w-xl text-sm leading-7 text-slate-400 sm:text-base">
                    Welcome{" "}
                    {user?.name || "back"}.
                    CareerPilot AI connects
                    specialized agents to help
                    with resumes, jobs,
                    interviews and career
                    planning.
                  </p>

                  <div className="mt-10 grid w-full max-w-3xl gap-3 sm:grid-cols-2">
                    <button
                      onClick={() =>
                        handleQuickAction(
                          "Review my resume and suggest improvements for a software developer role."
                        )
                      }
                      className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-cyan-400/30 hover:bg-cyan-400/5"
                    >
                      <div className="mb-2 text-lg">
                        📄
                      </div>

                      <div className="text-sm font-semibold">
                        Improve my resume
                      </div>

                      <div className="mt-1 text-xs text-slate-500">
                        Get ATS and content
                        improvement suggestions
                      </div>
                    </button>

                    <button
                      onClick={() =>
                        handleQuickAction(
                          "Suggest software developer job roles suitable for a fresher."
                        )
                      }
                      className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-blue-400/30 hover:bg-blue-400/5"
                    >
                      <div className="mb-2 text-lg">
                        💼
                      </div>

                      <div className="text-sm font-semibold">
                        Find suitable roles
                      </div>

                      <div className="mt-1 text-xs text-slate-500">
                        Explore career options
                        based on your skills
                      </div>
                    </button>

                    <button
                      onClick={() =>
                        handleQuickAction(
                          "Give me 10 Python interview questions for a fresher with answers."
                        )
                      }
                      className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-violet-400/30 hover:bg-violet-400/5"
                    >
                      <div className="mb-2 text-lg">
                        🎯
                      </div>

                      <div className="text-sm font-semibold">
                        Prepare for interview
                      </div>

                      <div className="mt-1 text-xs text-slate-500">
                        Practice technical and
                        HR questions
                      </div>
                    </button>

                    <button
                      onClick={() =>
                        handleQuickAction(
                          "Create a 30 day roadmap to become a full stack developer."
                        )
                      }
                      className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-purple-400/30 hover:bg-purple-400/5"
                    >
                      <div className="mb-2 text-lg">
                        🚀
                      </div>

                      <div className="text-sm font-semibold">
                        Create a learning roadmap
                      </div>

                      <div className="mt-1 text-xs text-slate-500">
                        Build a structured skill
                        development plan
                      </div>
                    </button>
                  </div>
                </div>
              )}

              <div className="space-y-6">
                {messages.map(
                  (message, index) => {
                    const isUser =
                      message.role === "user"

                    return (
                      <div
                        key={
                          message.id ??
                          `${message.role}-${index}`
                        }
                        className={`flex ${
                          isUser
                            ? "justify-end"
                            : "justify-start"
                        }`}
                      >
                        <div
                          className={`flex max-w-[90%] gap-3 sm:max-w-[80%] ${
                            isUser
                              ? "flex-row-reverse"
                              : ""
                          }`}
                        >
                          <div
                            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
                              isUser
                                ? "bg-blue-600"
                                : "bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-600"
                            }`}
                          >
                            {isUser
                              ? "YOU"
                              : "AI"}
                          </div>

                          <div>
                            {!isUser &&
                              message.agent_name && (
                                <div className="mb-1.5 text-[11px] font-medium text-cyan-400">
                                  {
                                    message.agent_name
                                  }
                                </div>
                              )}

                            <div
                              className={`rounded-2xl px-4 py-3 text-sm leading-7 ${
                                isUser
                                  ? "rounded-tr-sm bg-blue-600 text-white"
                                  : "rounded-tl-sm border border-white/10 bg-white/[0.04] text-slate-200"
                              }`}
                            >
                              <div className="whitespace-pre-wrap">
                                {
                                  message.content
                                }
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  }
                )}

                {loading && (
                  <div className="flex justify-start">
                    <div className="flex gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-600 text-xs font-bold">
                        AI
                      </div>

                      <div className="rounded-2xl rounded-tl-sm border border-white/10 bg-white/[0.04] px-5 py-4">
                        <div className="flex items-center gap-1.5">
                          <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-400" />

                          <span className="h-2 w-2 animate-bounce rounded-full bg-blue-400 [animation-delay:-0.15s]" />

                          <span className="h-2 w-2 animate-bounce rounded-full bg-violet-400 [animation-delay:-0.3s]" />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* =================================================
              INPUT
          ================================================= */}

          <div className="sticky bottom-0 border-t border-white/10 bg-slate-950/80 px-4 py-4 backdrop-blur-xl sm:px-6 lg:px-8">
            <div className="mx-auto max-w-5xl">
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-2 shadow-2xl focus-within:border-cyan-400/30">
                <div className="flex items-end gap-2">
                  <textarea
                    value={input}
                    onChange={(event) =>
                      setInput(
                        event.target.value
                      )
                    }
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                    rows={1}
                    placeholder="Ask CareerPilot AI anything about your career..."
                    className="max-h-40 min-h-[46px] flex-1 resize-none bg-transparent px-3 py-3 text-sm text-white outline-none placeholder:text-slate-600"
                  />

                  <button
                    onClick={() =>
                      sendMessage()
                    }
                    disabled={
                      loading ||
                      !input.trim()
                    }
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-lg font-bold transition hover:scale-105 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    ↑
                  </button>
                </div>
              </div>

              <div className="mt-2 flex items-center justify-between px-1">
                <p className="text-[10px] text-slate-600">
                  Press Enter to send ·
                  Shift + Enter for new line
                </p>

                {currentSessionId && (
                  <p className="text-[10px] text-slate-600">
                    Session #{currentSessionId}
                  </p>
                )}
              </div>
            </div>
          </div>
        </main>

        {/* =================================================
            RIGHT PANEL
        ================================================= */}

        <aside className="hidden w-80 shrink-0 border-l border-white/10 bg-slate-950/50 p-5 xl:block">
          <div className="sticky top-24">
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">
              Live Intelligence
            </p>

            <h3 className="mt-2 text-lg font-bold">
              Agent Control
            </h3>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              Your request is routed to the
              most relevant specialist.
            </p>

            <div className="mt-5 space-y-3">
              <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">
                    Router Agent
                  </span>

                  <span className="text-[10px] text-emerald-400">
                    ACTIVE
                  </span>
                </div>

                <div className="mt-2 text-sm font-semibold">
                  Intent Detection
                </div>

                <div className="mt-2 rounded-lg bg-black/20 px-3 py-2 text-xs text-cyan-300">
                  {activeIntent}
                </div>
              </div>

              <div className="flex justify-center text-slate-700">
                ↓
              </div>

              <div className="rounded-2xl border border-violet-400/20 bg-violet-400/5 p-4">
                <div className="text-xs text-slate-400">
                  Specialist
                </div>

                <div className="mt-2 text-sm font-semibold">
                  {activeAgent}
                </div>
              </div>

              <div className="flex justify-center text-slate-700">
                ↓
              </div>

              <div className="rounded-2xl border border-blue-400/20 bg-blue-400/5 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">
                    Gemini
                  </span>

                  <span className="text-[10px] text-emerald-400">
                    ONLINE
                  </span>
                </div>

                <div className="mt-2 text-sm font-semibold">
                  Response Generation
                </div>
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  PostgreSQL Memory
                </span>

                <span className="text-xs text-emerald-400">
                  ● Connected
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2">
                <div className="rounded-xl bg-black/20 p-3">
                  <div className="text-lg font-bold">
                    {sessions.length}
                  </div>

                  <div className="text-[10px] text-slate-500">
                    Sessions
                  </div>
                </div>

                <div className="rounded-xl bg-black/20 p-3">
                  <div className="text-lg font-bold">
                    {messages.length}
                  </div>

                  <div className="text-[10px] text-slate-500">
                    Current Msgs
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                Architecture
              </p>

              <div className="space-y-2 text-xs text-slate-500">
                <div>● React + TypeScript</div>
                <div>● Flask REST API</div>
                <div>● JWT Authentication</div>
                <div>● LangGraph Multi-Agent</div>
                <div>● Gemini LLM</div>
                <div>● PostgreSQL Memory</div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

export default App