const KNOWN_TERMS = [
  "semi-supervised learning", "unsupervised learning", "supervised learning",
  "reinforcement learning", "machine learning", "deep learning", "linear regression",
  "logistic regression", "decision tree", "random forest", "support vector machine",
  "gradient descent", "confusion matrix", "cross validation", "overfitting",
  "underfitting", "operating system", "context switch", "virtual memory",
  "deadlock", "race condition", "primary key", "foreign key", "normalization",
  "transaction", "binary search", "linked list", "hash table", "stack", "queue",
  "depth first search", "breadth first search", "computer network",
  "domain name system", "conditional probability", "bayes theorem"
];

const STOPWORDS = new Set([
  "a", "an", "the", "and", "or", "but", "if", "than", "to", "of", "in", "on",
  "for", "from", "by", "with", "as", "at", "is", "are", "was", "were", "be",
  "been", "it", "this", "that", "what", "which", "who", "when", "where", "why",
  "how", "does", "did", "can", "could", "would", "should", "will", "about",
  "into", "over", "under", "through", "your", "you", "we", "our", "they",
  "their", "them", "not", "also", "such", "using", "use", "used", "notes", "note"
]);

function textFromMessages(messages) {
  if (!Array.isArray(messages)) return "";
  return messages.map(function (message) {
    const content = message && message.content;
    if (typeof content === "string") return content;
    if (content && typeof content.text === "string") return content.text;
    if (Array.isArray(content)) {
      return content.filter(function (part) {
        return part && typeof part.text === "string";
      }).map(function (part) { return part.text; }).join("\n");
    }
    return "";
  }).filter(Boolean).join("\n\n").trim();
}

function cleanMaterial(value) {
  return String(value || "")
    .replace(/---\s*Source file:[\s\S]*?---/gi, " ")
    .replace(/<\/?study_material>/gi, " ")
    .replace(/\r/g, "\n")
    .replace(/[ \t]+/g, " ")
    .trim();
}

function extractMaterial(prompt) {
  const match = prompt.match(/<study_material>\s*([\s\S]*?)\s*<\/study_material>/i);
  return match ? cleanMaterial(match[1]) : "";
}

function statementsFrom(material) {
  if (!cleanMaterial(material)) return [];
  const parts = cleanMaterial(material).split(/\n+|;\s+|(?<=[.!?])\s+(?=[A-Z0-9])/)
    .map(function (item) {
      return item.replace(/^\s*(?:(?:\d+\.)+|\d+[.)]|[-*•])\s*/, "").replace(/\s+/g, " ").trim();
    })
    .filter(function (item) {
      return item.length >= 16 && !/^Source (?:file|basis):/i.test(item);
    });
  const seen = new Set();
  return parts.filter(function (item) {
    const key = item.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function termFromLeft(left) {
  let term = String(left || "").replace(/^\s*(?:\d+(?:\.\d+)*[.)]?\s*)/, "").trim();
  for (const known of KNOWN_TERMS) {
    if (term.toLowerCase().endsWith(known.toLowerCase())) return term.slice(term.length - known.length);
  }
  if (term.length > 60 || term.split(/\s+/).length > 5) {
    term = term.split(/\s+/).slice(-3).join(" ");
  }
  return term.replace(/^[\s,;:.-]+|[\s,;:.-]+$/g, "").trim();
}

function extractConcepts(material) {
  const concepts = [];
  const seen = new Set();
  for (const statement of statementsFrom(material)) {
    let match = statement.match(/^(.{2,90}?)\s+(?:is defined as|is described as|refers to|means|is an?|are)\s+(.{10,240})$/i);
    if (!match) match = statement.match(/^(.{2,90}?)\s*[—–:]\s*(.{10,240})$/);
    if (!match) continue;
    const term = termFromLeft(match[1]);
    const definition = match[2].replace(/[.;,\s]+$/g, "").trim();
    const key = term.toLowerCase();
    if (!term || term.length > 60 || term.split(/\s+/).length > 5 ||
        definition.length < 10 || seen.has(key) ||
        /^(source file|source basis)$/i.test(term)) continue;
    seen.add(key);
    concepts.push({ term: term, definition: definition.slice(0, 240) });
    if (concepts.length >= 40) break;
  }
  return concepts;
}

function getField(prompt, label, fallback) {
  const match = prompt.match(new RegExp("^" + label + ":\\s*(.+)$", "im"));
  return match ? match[1].trim() : fallback;
}

function topicSequence(material, subject) {
  const concepts = extractConcepts(material);
  if (concepts.length) return concepts.map(function (item) { return item.term; });
  const statements = statementsFrom(material);
  if (statements.length) return statements.slice(0, 18).map(function (item) {
    return item.length > 88 ? item.slice(0, 85).trimEnd() + "…" : item;
  });
  return [
    "Core terms and prerequisites for " + subject,
    "Foundational concepts and their relationships",
    "Worked examples and problem-solving steps",
    "Common applications and question types",
    "Active recall of definitions and formulas",
    "Mixed practice and error correction",
    "Cumulative revision and a timed checkpoint"
  ];
}

function generateStudyPlan(prompt) {
  const subject = getField(prompt, "Subject", "your subject");
  const level = getField(prompt, "Current level", "Intermediate");
  const weeks = Math.max(1, Math.min(12, Number((prompt.match(/Duration:\s*(\d+)\s*weeks/i) || [])[1]) || 4));
  const hours = Math.max(0.5, Math.min(8, Number((prompt.match(/Available study time:\s*([\d.]+)/i) || [])[1]) || 2));
  const goals = getField(prompt, "Learning goals", "Build understanding and practise questions.");
  const topics = topicSequence(extractMaterial(prompt), subject);
  const minutes = Math.round(hours * 60);
  const learn = Math.round(minutes * 0.35);
  const practice = Math.round(minutes * 0.30);
  const recall = Math.round(minutes * 0.20);
  const review = Math.max(5, minutes - learn - practice - recall);
  const lines = [
    "# Study plan: " + subject, "",
    "> Offline mode: this plan is built in your browser from your settings and extracted notes. It does not use a hosted AI model; check the sequence against your syllabus.", "",
    "**Level:** " + level + "  ", "**Duration:** " + weeks + " week(s)  ",
    "**Daily time:** " + hours + " hour(s)  ", "**Goal:** " + goals, ""
  ];
  for (let week = 0; week < weeks; week += 1) {
    lines.push("## Week " + (week + 1) + ": " + topics[(week * 3) % topics.length], "");
    lines.push("*Focus: understand the ideas, practise retrieval, and revisit earlier topics.*", "");
    for (let day = 0; day < 7; day += 1) {
      const topic = topics[(week * 7 + day) % topics.length];
      if (day === 6) {
        const recallTime = Math.round(minutes * 0.45);
        const practiceTime = Math.round(minutes * 0.35);
        lines.push("7. **Day 7 — Weekly checkpoint and catch-up** — " +
          recallTime + " min closed-book recall, " + practiceTime +
          " min mixed practice, and " + Math.max(5, minutes - recallTime - practiceTime) +
          " min correcting errors and planning next week.");
      } else {
        lines.push((day + 1) + ". **Day " + (day + 1) + " — " + topic +
          "** — learn or review (" + learn + " min), solve examples (" + practice +
          " min), recall definitions without notes (" + recall +
          " min), and revisit mistakes (" + review + " min).");
      }
    }
    lines.push("", "**Weekly checkpoint:** explain the main ideas without notes, do a short mixed practice set, and move unfinished topics into next week's catch-up block.", "");
  }
  lines.push("## Adjusting when you fall behind", "",
    "Keep the daily time limit. Prioritise prerequisites and repeated mistakes, shorten optional reading, and use the next checkpoint to choose what needs another session. Do not stack missed hours on top of tomorrow's workload.");
  return lines.join("\n");
}

function generateSummary(material) {
  const sentences = statementsFrom(material);
  const concepts = extractConcepts(material);
  const lines = [
    "# Offline study summary", "",
    "> Created in your browser from the supplied text using extractive rules, without an external AI API. Verify details against the original notes.", "",
    "## 1. Overview", "", sentences.slice(0, 2).join(" ") || "No readable text was extracted.", "",
    "## 2. Key concepts and facts", ""
  ];
  if (concepts.length) {
    concepts.slice(0, 12).forEach(function (item) { lines.push("- **" + item.term + ":** " + item.definition + "."); });
  } else if (sentences.length) {
    sentences.slice(0, 10).forEach(function (item) { lines.push("- " + item); });
  } else lines.push("- No key facts could be extracted.");
  const examples = sentences.filter(function (item) {
    return /\b(example|for instance|formula|algorithm|step \d+|procedure|equation|e\.g\.)\b/i.test(item);
  }).slice(0, 6);
  lines.push("", "## 3. Examples, formulas, or steps mentioned", "",
    examples.length ? examples.map(function (item) { return "- " + item; }).join("\n") :
      "No examples were clearly labelled in the extracted text. Check the original document for diagrams and worked examples.",
    "", "## 4. Points to check carefully", "");
  if (concepts.length >= 2) lines.push("- Compare **" + concepts[0].term + "** and **" + concepts[1].term + "** and state how their definitions differ.");
  lines.push("- Verify formulas, symbols, assumptions, and exceptions against the source.",
    "- PDF text extraction may flatten tables or diagrams; inspect them in the original file.",
    "", "## 5. Revision checklist", "");
  concepts.slice(0, 8).forEach(function (item) { lines.push("- [ ] Define " + item.term + " and give a course example."); });
  if (!concepts.length) lines.push("- [ ] Write the main idea of each section and identify terms that need clarification.");
  lines.push("", "## Self-test questions", "");
  const questions = concepts.slice(0, 5).map(function (item) { return "What is " + item.term + ", according to the notes?"; });
  while (questions.length < 5 && sentences.length > questions.length) {
    questions.push("Explain this point in your own words: \"" + sentences[questions.length].slice(0, 110) + "\".");
  }
  while (questions.length < 5) questions.push("Which idea from the source needs another review, and why?");
  questions.slice(0, 5).forEach(function (item, index) { lines.push((index + 1) + ". " + item); });
  return lines.join("\n");
}

function explainConcepts(material) {
  const concepts = extractConcepts(material);
  const sentences = statementsFrom(material);
  const lines = ["# Explain concepts — offline mode", "",
    "> This uses definitions and statements found in your notes. It does not infer missing details with a hosted language model.", ""];
  if (concepts.length) {
    concepts.slice(0, 18).forEach(function (item, index) {
      lines.push("## " + (index + 1) + ". " + item.term, "", item.definition + ".", "",
        "**Check your understanding:** explain this definition in your own words and connect it to a course example.", "");
    });
  } else if (sentences.length) {
    lines.push("The text does not contain enough clearly formatted term-definition pairs for automatic extraction. Key statements to review:", "");
    sentences.slice(0, 15).forEach(function (item) { lines.push("- " + item); });
  } else lines.push("No readable source text was found. Paste or upload readable notes and try again.");
  return lines.join("\n");
}

function tokenize(value) {
  return String(value || "").toLowerCase().match(/[a-z0-9]+/g) || [];
}

function answerQuestion(prompt) {
  const material = extractMaterial(prompt);
  const questionMatch = prompt.match(/Student's question:\s*([\s\S]*?)(?:\n|$)/i);
  const question = questionMatch ? questionMatch[1].trim() : "";
  const sentences = statementsFrom(material);
  const terms = Array.from(new Set(tokenize(question).filter(function (word) {
    return word.length > 2 && !STOPWORDS.has(word);
  })));
  const scored = sentences.map(function (sentence) {
    const words = new Set(tokenize(sentence));
    const overlap = terms.filter(function (word) { return words.has(word); });
    return { sentence: sentence, score: overlap.length, overlap: overlap };
  }).filter(function (item) { return item.score > 0; })
    .sort(function (a, b) { return b.score - a.score; }).slice(0, 4);
  const lines = ["# Answer from your notes — offline mode", "",
    "> This is a keyword-matched answer from the supplied text, not a semantic AI answer. It can miss relevant passages when wording differs.", ""];
  if (!question) return "Enter a question first.";
  if (!scored.length) {
    lines.push("I could not find a clear keyword match in the supplied notes, so I cannot give a reliable source-grounded answer in offline mode.",
      "", "**Question:** " + question, "",
      "Try the exact term or heading used in your notes, or check the original material.");
    return lines.join("\n");
  }
  lines.push("**Question:** " + question, "", "Closest matching passages:", "");
  scored.forEach(function (item) { lines.push("- " + item.sentence); });
  lines.push("", "**Terms matched:** " + Array.from(new Set(scored.flatMap(function (item) { return item.overlap; }))).join(", "),
    "", "Compare these passages with their surrounding paragraphs before treating them as a complete answer.");
  return lines.join("\n");
}

const BANKS = [
  { match: /machine learning|\bml\b|artificial intelligence|\bai\b/i, title: "Machine Learning", questions: [
    ["Which learning setup uses labelled examples?", ["Supervised learning", "Unsupervised learning", "Reinforcement learning", "Clustering"], 0, "Supervised learning uses input examples paired with target labels."],
    ["Which task predicts a continuous numerical value?", ["Regression", "Classification", "Clustering", "Tokenization"], 0, "Regression predicts numerical targets."],
    ["Which task predicts a discrete category?", ["Classification", "Regression", "Sampling", "Normalization"], 0, "Classification predicts discrete labels."],
    ["What is overfitting?", ["Fitting training data closely but generalizing poorly", "Always using too few parameters", "Removing every training example", "Scaling all features"], 0, "Overfitting captures training-specific patterns that may not generalize."],
    ["What is a feature?", ["An input variable used for a prediction", "Always the final prediction", "Only the learning rate", "A hidden test label"], 0, "Features are input attributes used by a predictive model."],
    ["What does clustering aim to do?", ["Group similar examples without requiring class labels", "Predict only continuous targets", "Guarantee causation", "Sort records by date"], 0, "Clustering groups data points by similarity."],
    ["What does gradient descent do?", ["Updates parameters using gradient information", "Creates labels for every example", "Always increases loss", "Sorts a dataset"], 0, "Gradient descent adjusts parameters to reduce an objective."],
    ["What does a confusion matrix summarize?", ["Predicted versus actual class counts", "The model file size", "Column order", "Only training time"], 0, "A confusion matrix compares predicted and actual classes."],
    ["What is data leakage?", ["Using information unavailable at prediction time during training or evaluation", "Shuffling training examples", "Saving a clean test set", "Renaming columns"], 0, "Leakage can produce misleadingly high evaluation scores."],
    ["Why use a held-out test set?", ["Estimate generalization on unseen data", "Fit the model repeatedly", "Guarantee zero error", "Replace all training data"], 0, "A held-out test set is an independent evaluation when used correctly."]
  ]},
  { match: /operating systems|\bos\b|process scheduling|virtual memory/i, title: "Operating Systems", questions: [
    ["What is a process?", ["A program in execution with state and resources", "A file extension", "Only a CPU register", "An IP address"], 0, "A process is an executing program with its state and resources."],
    ["What is a thread?", ["An execution path within a process", "A disk partition", "A database row", "A routing protocol"], 0, "Threads are execution units within a process."],
    ["What happens in a context switch?", ["One execution state is saved and another restored", "The scheduler is deleted", "All files are compressed", "The clock always doubles"], 0, "A context switch changes the execution context running on a CPU."],
    ["What describes deadlock?", ["Processes wait indefinitely for resources held by one another", "A process completes normally", "A file is compressed", "A program compiles"], 0, "Deadlock is a resource-wait condition that prevents progress."],
    ["What is virtual memory for?", ["Providing virtual address spaces backed by memory-management mechanisms", "Encrypting packets", "Replacing the scheduler", "Compiling SQL"], 0, "Virtual memory provides processes with virtual address spaces."],
    ["What does a CPU scheduler choose?", ["Which ready task runs next", "Which files are renamed", "Which DNS record is valid", "Which database rows are primary keys"], 0, "The scheduler selects work according to a scheduling policy."],
    ["What does a mutex provide?", ["Mutual exclusion around a shared resource", "Guaranteed packet delivery", "Database normalization", "Memory prediction"], 0, "A mutex coordinates exclusive access to a critical section."],
    ["What is a race condition?", ["Behavior depends on timing or ordering of concurrent operations", "A sorting method", "A memory address", "A file format"], 0, "Race conditions occur when concurrent ordering affects results."],
    ["What is paging?", ["Dividing address space into fixed-size pages mapped to frames", "Scheduling by name", "Compressing a table", "Sending packets without addresses"], 0, "Paging maps virtual pages to physical frames."],
    ["What is a system call?", ["A request for an operating-system service", "A database index", "A code comment", "A DNS record"], 0, "Programs use system calls to request kernel services."]
  ]},
  { match: /database|dbms|\bsql\b|normalization|acid transaction/i, title: "Databases and DBMS", questions: [
    ["What does a primary key do?", ["Uniquely identifies a row", "Stores passwords in plain text", "Allows duplicate values by design", "Connects only to a browser"], 0, "A primary key uniquely identifies a row and cannot be null."],
    ["What is a foreign key used for?", ["Referencing a key in another or the same table", "Sorting only in memory", "Encrypting a database", "Replacing all columns"], 0, "Foreign keys represent referential relationships."],
    ["Why normalize a database?", ["Reduce redundancy and update anomalies", "Increase duplicate data", "Remove all relationships", "Avoid keys"], 0, "Normalization structures relations to reduce redundancy."],
    ["What does atomicity mean in ACID?", ["A transaction is all-or-nothing", "Queries run alphabetically", "Data uses one column", "All transactions are read-only"], 0, "Atomicity means a transaction commits completely or is rolled back."],
    ["What does SQL SELECT do?", ["Retrieves rows or expressions", "Always deletes a table", "Creates a network connection", "Formats a CPU instruction"], 0, "SELECT is used to query data."],
    ["What is an index intended to improve?", ["Finding rows for selected queries", "Guaranteeing writes never happen", "Removing the schema", "Making every query constant-time"], 0, "Indexes can speed lookups but use storage and add write overhead."],
    ["What does JOIN do?", ["Combines related rows using a condition", "Deletes all duplicates automatically", "Changes a password", "Compiles Python"], 0, "JOIN combines rows according to a specified relationship."],
    ["What is a transaction?", ["A logical unit of database work", "A network cable", "A model feature", "A sorting loop"], 0, "Transactions group related database operations."],
    ["What does consistency mean in ACID?", ["Committed work preserves database constraints", "Every user has a different schema", "Transactions never read data", "Queries have identical runtime"], 0, "Consistency means transactions preserve defined invariants."],
    ["What is an index's common trade-off?", ["Faster reads for some queries but extra storage and write cost", "Faster writes with no storage", "It removes the need for keys", "It ensures every query takes one step"], 0, "Indexes trade storage and maintenance cost for some faster queries."]
  ]},
  { match: /data structures|algorithms|\bdsa\b|binary search|linked list|big.?o/i, title: "Data Structures and Algorithms", questions: [
    ["Which principle does a stack follow?", ["Last in, first out (LIFO)", "First in, first out (FIFO)", "Random access only", "Smallest item first"], 0, "The last pushed item is normally popped first."],
    ["Which principle does a queue follow?", ["First in, first out (FIFO)", "Last in, first out (LIFO)", "Highest priority only", "Reverse alphabetically"], 0, "A standard queue removes items in arrival order."],
    ["What condition does binary search require?", ["An ordered search range", "All items must be files", "The array must be a linked list", "The target must be first"], 0, "Binary search repeatedly halves an ordered range."],
    ["What is a linked-list node?", ["Data with one or more links to other nodes", "A scheduler", "A SQL keyword", "An encryption key"], 0, "Nodes hold values and references or links."],
    ["What is average-case lookup often associated with a well-behaved hash table?", ["O(1)", "O(n squared) in every case", "O(n factorial)", "O(1) for all worst cases"], 0, "Hash-table lookup is expected constant time under suitable assumptions."],
    ["How does breadth-first search explore?", ["Level by level, typically with a queue", "Only the deepest path first", "Alphabetically", "Without tracking visited nodes"], 0, "BFS explores vertices in distance layers."],
    ["What is a common merge sort complexity?", ["O(n log n)", "O(n squared) in every implementation", "O(log n) for all inputs", "O(1)"], 0, "Merge sort divides then merges sorted parts in O(n log n) time."],
    ["What does Big-O describe?", ["Asymptotic upper growth", "Exact runtime on every computer", "Only storage in bytes", "Proof that code has no bugs"], 0, "Big-O describes growth rather than exact wall-clock time."],
    ["What does depth-first search do?", ["Explore a path deeply before backtracking", "Visit in increasing distance", "Require sorted arrays", "Only work on databases"], 0, "DFS explores deeply along a path before backtracking."],
    ["What is a priority queue designed to retrieve?", ["An item selected by priority", "Always the oldest item regardless of priority", "Only the last inserted item", "A random field"], 0, "A priority queue selects according to its priority rule."]
  ]},
  { match: /computer network|networking|\btcp\b|\budp\b|\bdns\b|http protocol/i, title: "Computer Networks", questions: [
    ["What does DNS primarily do?", ["Resolves domain names to records such as IP addresses", "Encrypts every disk file", "Schedules CPU threads", "Normalizes tables"], 0, "DNS resolves names using resource records."],
    ["Which describes TCP?", ["Connection-oriented transport with reliable ordered delivery", "No sequence or delivery mechanisms", "A graphics API", "A normal form"], 0, "TCP provides reliable ordered delivery over a connection."],
    ["Which describes UDP?", ["Connectionless datagram transport without built-in delivery guarantees", "A database key", "A sorting algorithm", "A compression format"], 0, "UDP lacks TCP's built-in reliability and ordering guarantees."],
    ["What is IP routing for?", ["Forwarding packets between networks", "Generating study plans", "Storing passwords", "Normalizing tables"], 0, "Routers forward packets toward destination networks."],
    ["What is HTTP?", ["An application-layer protocol for web communication", "A disk scheduler", "A loss function", "A programming type"], 0, "HTTP defines request-response semantics for web applications."],
    ["What does TLS commonly provide?", ["Encryption and integrity, often with server authentication", "Zero latency", "Automatic compilation", "Database indexing"], 0, "TLS protects data in transit and can authenticate the server."],
    ["What is an IP address for?", ["Network-layer addressing for packet delivery", "A function argument", "Model accuracy", "A database index"], 0, "IP addresses support packet addressing and routing."],
    ["What does a router generally do?", ["Forward packets between networks", "Apply CSS", "Replace transport protocols", "Store one SQL row"], 0, "Routers connect networks and forward packets."],
    ["What is latency?", ["Delay for data or a request to travel and be processed", "Number of table columns", "Integer capacity", "Queue ordering"], 0, "Latency measures delay, unlike throughput."],
    ["What is client-server architecture?", ["Clients request services or resources from servers", "All programs run in one register", "A database has no users", "Traffic is always encrypted"], 0, "Clients initiate requests and servers provide services."]
  ]},
  { match: /python|programming language|functions|exception handling/i, title: "Programming and Python", questions: [
    ["Which Python collection is ordered and mutable?", ["list", "tuple", "str", "frozenset"], 0, "Python lists are ordered and mutable."],
    ["What does a Python dictionary store?", ["Key-value mappings", "Only duplicate values in a fixed sequence", "Only numeric arrays", "Only gradients"], 0, "Dictionaries map keys to values."],
    ["What is try/except used for?", ["Handle selected exceptions", "Guarantee no bugs", "Declare a primary key", "Create a network route"], 0, "try/except lets code respond to exceptions."],
    ["What is recursion?", ["A function or process calls itself directly or indirectly", "A list is sorted", "A table is joined", "Every loop runs once"], 0, "Recursive solutions need a stopping condition."],
    ["Which Python type is immutable?", ["tuple", "list", "dict", "set"], 0, "Tuples cannot be changed in place."],
    ["What does a set store?", ["Distinct elements", "A sequence with all duplicates by position", "Mandatory pairs of values", "File handles only"], 0, "Sets store unique hashable elements."],
    ["What is a function useful for?", ["Encapsulating reusable operations", "Guaranteeing valid input", "Replacing the OS", "Encrypting memory"], 0, "Functions create reusable callable units."],
    ["Why validate external input?", ["Check type, format, and range before using values", "Make all errors impossible", "Improve CPU clock speed", "Remove the need for tests"], 0, "Validation checks whether input meets required constraints."],
    ["What is a recursive base case?", ["A condition that returns without further recursive calls", "A table column", "The largest possible stack", "An import statement"], 0, "A base case stops the recursive chain."],
    ["What is an algorithm?", ["A defined procedure for solving a problem", "Always a machine-learning model", "A storage device", "A language keyword"], 0, "An algorithm specifies steps that transform inputs into outputs."]
  ]},
  { match: /probability|statistics|bayes|standard deviation|conditional probability/i, title: "Probability and Statistics", questions: [
    ["What is the arithmetic mean?", ["Sum of values divided by the number of values", "Always the most common value", "Maximum minus minimum", "Square root of sample size"], 0, "The arithmetic mean is sum divided by count."],
    ["What is the median?", ["Middle ordered value, or mean of two middle values for an even count", "Always the mode", "Always the maximum", "Total divided by variance"], 0, "The median is a positional measure of central tendency."],
    ["What does variance measure?", ["Spread using squared deviations from the mean", "Only record count", "Most frequent value", "An event name"], 0, "Variance measures dispersion using squared deviations."],
    ["What does P(A|B) mean?", ["Probability of A given B occurred", "Probability A and B can never occur", "Only the complement of B", "The average of A and B"], 0, "Conditional probability conditions on event B."],
    ["When are two events independent?", ["P(A and B) = P(A)P(B)", "Only when they are mutually exclusive with positive probability", "Their probabilities sum to zero", "A occurs first"], 0, "Independence means one event does not change the other's probability."],
    ["What is the sample space?", ["The set of possible outcomes in an experiment", "Only the most likely result", "The mean", "A regression coefficient"], 0, "The sample space contains the outcomes represented by the probability model."],
    ["What is standard deviation?", ["The square root of variance", "The square of the mean", "Always the number of categories", "The sum of probabilities"], 0, "Standard deviation expresses dispersion on the original scale."],
    ["What is the complement of A?", ["The event that A does not occur", "The intersection of A with itself only", "Always an impossible event", "The sample mean"], 0, "The complement contains outcomes outside A."],
    ["What does Bayes' theorem relate?", ["A posterior probability to a likelihood and a prior", "A stack to a queue", "Binary search complexity", "A row to a primary key"], 0, "Bayes' theorem updates probability using prior information and likelihood."],
    ["For a fair six-sided die, what is the probability of rolling a 6?", ["1/6", "1/2", "1/3", "5/6"], 0, "One of six equally likely outcomes is a six."]
  ]}
];

const GENERAL_QUESTIONS = [
  ["What is active recall?", ["Trying to retrieve information before looking at the answer", "Highlighting every sentence", "Copying a paragraph verbatim", "Avoiding self-tests"], 0, "Active recall involves retrieving information from memory."],
  ["What is spaced revision?", ["Reviewing material in sessions separated over time", "Studying everything only at the last minute", "Repeating one item immediately forever", "Removing reviews"], 0, "Spacing distributes retrieval across time."],
  ["What should you do after a practice answer is wrong?", ["Analyse the error and retry a related question", "Hide the result", "Memorize only the option letter", "Never revisit the topic"], 0, "Error analysis and targeted retry provide useful feedback."],
  ["How should a long task be scheduled?", ["Split it into smaller sessions with concrete goals", "Make every session unlimited", "Skip practice until the final day", "Ignore available time"], 0, "Small specific sessions are easier to plan and evaluate."],
  ["What makes a practice quiz useful?", ["Questions test concepts and feedback explains answers", "Answers appear before each question", "All options are identical", "Mistakes are never reviewed"], 0, "Practice works best with retrieval and feedback."],
  ["How can you tell whether a plan is realistic?", ["Tasks fit the available time and leave room for review", "It assigns more hours than a day contains", "It has no checkpoints", "It contains reading only"], 0, "A realistic schedule respects constraints and includes practice."],
  ["When should you verify a summary against original notes?", ["When detail, context, formulas, or diagrams matter", "Never after a summary", "Only after an exam", "Only for page numbers"], 0, "Extractive tools can miss context and visual material."],
  ["Why mix older topics into newer practice?", ["Practise choosing methods and retain earlier knowledge", "Make every answer identical", "Avoid retrieval", "Stop tracking progress"], 0, "Mixed review exercises discrimination and revisits older material."],
  ["What belongs in a weekly checkpoint?", ["Review progress, errors, and next priorities", "Add all missed work to tomorrow", "Delete every difficult topic", "Avoid quiz results"], 0, "Checkpoints let you adjust a plan based on evidence."],
  ["What is a useful learning goal?", ["A specific skill or topic you can practise and check", "Study everything perfectly", "Never make errors", "Read without a time limit"], 0, "Specific goals are easier to schedule and evaluate."]
];

function makeQuestion(question, answer, distractors, explanation, index) {
  const wrong = [];
  for (const item of distractors || []) {
    const value = String(item || "").trim();
    if (value && value.toLowerCase() !== String(answer).toLowerCase() &&
        !wrong.some(function (existing) { return existing.toLowerCase() === value.toLowerCase(); })) wrong.push(value);
  }
  const generic = ["A concept unrelated to the question", "A statement not supported by the material", "A different concept from the course"];
  for (const item of generic) {
    if (wrong.length >= 3) break;
    if (item.toLowerCase() !== String(answer).toLowerCase() &&
        !wrong.some(function (existing) { return existing.toLowerCase() === item.toLowerCase(); })) wrong.push(item);
  }
  const options = wrong.slice(0, 3);
  const correctIndex = index % 4;
  options.splice(correctIndex, 0, String(answer));
  return { question: question, options: options, correct_index: correctIndex, explanation: explanation };
}

function generateQuiz(prompt) {
  const match = prompt.match(/Create exactly\s+(\d+)\s+multiple-choice questions about\s+(.+?)\s+at\s+(Easy|Medium|Hard)\s+difficulty/i);
  const count = Math.max(3, Math.min(10, Number(match && match[1]) || 5));
  const topic = (match && match[2] || "your subject").trim().replace(/[.]+$/, "");
  const material = extractMaterial(prompt);
  const concepts = extractConcepts(material);
  const sentences = statementsFrom(material);
  const questions = [];

  if (concepts.length) {
    for (let i = 0; i < count; i += 1) {
      const concept = concepts[i % concepts.length];
      const distractors = concepts.filter(function (item) {
        return item.term.toLowerCase() !== concept.term.toLowerCase();
      }).map(function (item) { return item.term; });
      questions.push(makeQuestion(
        "Which term matches this description from your notes: \"" + concept.definition + "\"?",
        concept.term,
        distractors.concat(["A term not defined in the notes", "An unrelated process", "A different course concept"]),
        "The extracted notes associate \"" + concept.term + "\" with: " + concept.definition + ".",
        i
      ));
    }
    return JSON.stringify({ title: "Offline note-based quiz: " + topic, questions: questions, mode: "offline" });
  }

  if (material && sentences.length) {
    for (let i = 0; i < count; i += 1) {
      const statement = sentences[i % sentences.length].slice(0, 210);
      questions.push(makeQuestion(
        "Which statement is explicitly supported by the supplied notes?",
        statement,
        ["The notes explicitly reject this statement.", "The notes say this topic is not covered.", "The notes state the opposite conclusion."],
        "This statement was extracted from the material; confirm its surrounding context in the original notes.",
        i
      ));
    }
    return JSON.stringify({ title: "Offline note-based quiz: " + topic, questions: questions, mode: "offline" });
  }

  const bank = BANKS.find(function (item) { return item.match.test(topic); });
  const items = bank ? bank.questions : GENERAL_QUESTIONS;
  for (let i = 0; i < count; i += 1) {
    const item = items[i % items.length];
    questions.push(makeQuestion(item[0], item[1][item[2]], item[1].filter(function (_, index) {
      return index !== item[2];
    }), item[3], i));
  }
  return JSON.stringify({
    title: bank ? bank.title + " — offline practice" : "Offline study-skills practice: " + topic,
    questions: questions,
    mode: "offline"
  });
}

export function generateOfflineStudyResponse(payload) {
  const prompt = textFromMessages(payload && payload.messages);
  if (!prompt) throw new Error("Enter a study request or some study material first.");
  if (/Create exactly\s+\d+\s+multiple-choice questions about/i.test(prompt)) return generateQuiz(prompt);
  if (/Create a practical, specific study plan for a student/i.test(prompt)) return generateStudyPlan(prompt);
  if (/Summarize the supplied document/i.test(prompt)) {
    const material = extractMaterial(prompt);
    if (!material) throw new Error("Paste or upload readable study material first.");
    return generateSummary(material);
  }
  if (/Teach the most important concepts from the supplied material/i.test(prompt)) {
    const material = extractMaterial(prompt);
    if (!material) throw new Error("Paste or upload readable study material first.");
    return explainConcepts(material);
  }
  if (/Answer the student's question using the supplied study material/i.test(prompt)) {
    const material = extractMaterial(prompt);
    if (!material) throw new Error("Paste or upload readable study material first.");
    return answerQuestion(prompt);
  }
  throw new Error("This action is not supported by the built-in offline study tools yet.");
}
