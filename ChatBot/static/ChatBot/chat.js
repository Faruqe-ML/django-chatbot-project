
document.addEventListener("DOMContentLoaded", () => {
    const promptInput = document.getElementById("promptInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatInner = document.getElementById("chatInner");
    const chatScroll = document.getElementById("chatScroll");
    const newChatBtn = document.getElementById("newChatBtn");
    const csrfInput = document.querySelector(
        "[name=csrfmiddlewaretoken]"
    );

    function addUserMessage(question) {
        const row = document.createElement("div");
        row.className = "chat-row user-row";

        const avatar = document.createElement("div");
        avatar.className = "avatar user-avatar";
        avatar.textContent = "👤";

        const bubble = document.createElement("div");
        bubble.className = "user-bubble";
        bubble.textContent = question;

        row.append(avatar, bubble);
        chatInner.appendChild(row);
        scrollToBottom();
    }

    function addAssistantResponse(data) {
    const row = document.createElement("div");
    row.className = "chat-row assistant-row";

    // AI Teacher logo image
    const avatar = document.createElement("div");
    avatar.className = "avatar ai-avatar";

    const aiImage = document.createElement("img");
    aiImage.src = "/static/ChatBot/robot-ai.png";
    aiImage.alt = "AI Teacher";
    aiImage.className = "ai-avatar-image";

    avatar.appendChild(aiImage);

    const response = document.createElement("div");
    response.className = "ai-response";

    // Subject name
    const subject = document.createElement("div");
    subject.className = "subject-badge";

    const subjectNames = {
        ml: "Machine Learning",
        machine_learning: "Machine Learning",
        dl: "Deep Learning",
        deep_learning: "Deep Learning",
        c_programming: "C Programming",
        dsa: "Data Structures & Algorithms",
        general: "General Knowledge"
    };

    subject.textContent =
        "📚 " + (subjectNames[data.topic] || "Learning Assistant");

    response.appendChild(subject);

    // Main answer, summary, and important points
    response.append(
        createSection(
            "📘",
            "Main Answer",
            data.answer || "No answer returned."
        ),
        createSection(
            "📝",
            "Summary",
            data.summary || "No summary returned."
        ),
        createSection(
            "💡",
            "Important Points",
            data.key_points || "No important points returned."
        )
    );

    row.append(avatar, response);
    chatInner.appendChild(row);
    scrollToBottom();
}


function createSection(icon, title, content) {
    const section = document.createElement("section");
    section.className = "answer-section";

    const heading = document.createElement("h3");
    heading.className = "section-heading";
    heading.textContent = `${icon} ${title}`;

    const body = document.createElement("div");
    body.className = "section-content";

    if (Array.isArray(content)) {
    const list = document.createElement("ul");
    list.className = "important-points-list";

    content.forEach(point => {
        const item = document.createElement("li");

        const text = String(point);

        if (
            typeof marked !== "undefined" &&
            typeof DOMPurify !== "undefined"
        ) {
            item.innerHTML = DOMPurify.sanitize(
                marked.parseInline(text)
            );
        } else {
            item.textContent = text;
        }

        list.appendChild(item);
    });

    body.appendChild(list);
} else {
    const markdown = String(content ?? "");

    if (
        typeof marked !== "undefined" &&
        typeof DOMPurify !== "undefined"
    ) {
        body.innerHTML = DOMPurify.sanitize(
            marked.parse(markdown, {
                breaks: true,
                gfm: true
            })
        );
    } else {
        body.textContent = markdown;
    }
}
    section.append(heading, body);
    return section;
}

    function scrollToBottom() {
        chatScroll.scrollTop = chatScroll.scrollHeight;
    }

    async function sendMessage() {
        const question = promptInput.value.trim();

        if (!question || sendBtn.disabled) return;

        addUserMessage(question);
        promptInput.value = "";
        sendBtn.disabled = true;

        const loading = document.createElement("div");
        loading.className = "loading-message";
        loading.textContent = "✦ AI is thinking...";
        chatInner.appendChild(loading);
        scrollToBottom();

        try {
            const response = await fetch("/chat/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfInput?.value || ""
                },
                body: JSON.stringify({ question })
            });

            const data = await response.json();
            displayRecentQuestions(data.recent_questions || []);
            if (!response.ok) {
                throw new Error(data.error || "Request failed.");
            }

            loading.remove();
            addAssistantResponse(data);

        } catch (error) {
            loading.textContent = `Error: ${error.message}`;
            console.error("Chat request failed:", error);
        } finally {
            sendBtn.disabled = false;
            promptInput.focus();
        }
    }

    sendBtn.addEventListener("click", sendMessage);

    promptInput.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    newChatBtn?.addEventListener("click", () => {
        chatInner.replaceChildren();
        promptInput.value = "";
        promptInput.focus();
    });

    console.log("AI chatbot JavaScript loaded successfully.");
});


function displayRecentQuestions(questions) {
    const list = document.getElementById("recentQuestions");

    list.innerHTML = "";

    if (!questions || questions.length === 0) {
        list.innerHTML =
            '<li class="empty-message">No recent questions</li>';
        return;
    }

    // Newest question first
    questions.forEach(question => {
        const li = document.createElement("li");
        const button = document.createElement("button");

        button.className = "recent-question";
        button.textContent = question;

        button.onclick = () => {
            promptInput.value = question;
            promptInput.focus();
        };

        li.appendChild(button);
        list.appendChild(li);
    });
}