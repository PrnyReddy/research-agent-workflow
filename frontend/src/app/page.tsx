"use client";

import React, { useState, FormEvent, ChangeEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import {
  Upload,
  Search,
  BrainCircuit,
  FileText,
  Loader,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  CircularProgress,
  Box,
  Alert,
  Snackbar,
  Tooltip,
  IconButton,
  Collapse,
} from "@mui/material";

interface AgentData {
  research_data?: string[];
  analysis?: string | Record<string, any>;
  report?: string | Record<string, any>;
}

interface AgentOutput {
  agent: string;
  type: 'research_data' | 'analysis' | 'report' | 'error';
  content: string;
}

const titles: Record<string, string> = {
  researcher: "Researcher",
  analyst: "Analyst",
  report_writer: "Final Report",
  error: "Error",
};

const icons: Record<string, React.ReactNode> = {
  researcher: <Search size={24} color="#1976d2" />,
  analyst: <BrainCircuit size={24} color="#1976d2" />,
  report_writer: <FileText size={24} color="#1976d2" />,
  error: <FileText size={24} color="red" />,
};

function extractMarkdown(content: string): string {
  if (typeof content === "string" && content.startsWith("```")) {
    return content.replace(/```[\w]*\n?/, "").replace(/```$/, "").trim();
  }
  return content;
}

function parseJsonCodeBlock(content: string): Record<string, any> | string {
  if (typeof content === "string" && content.startsWith("```json")) {
    try {
      const jsonMatch = content.match(/```json\s*([\s\S]+?)```/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[1]);
      }
    } catch (e) {
      console.error("Failed to parse JSON code block:", e);
    }
  }
  return content;
}

function formatReportToMarkdown(reportObj: any): string {
  if (!reportObj || typeof reportObj !== "object") return "";
  let markdown = "";
  if (reportObj.key_insights) markdown += `## Key Insights\n\n${reportObj.key_insights}\n\n`;
  if (reportObj.comparative_analysis) markdown += `## Comparative Analysis\n\n${reportObj.comparative_analysis}\n\n`;
  if (reportObj.narrative) markdown += `## Narrative\n\n${reportObj.narrative}\n\n`;
  return markdown.trim();
}

const normalizeOutput = (
  agent: string,
  type: 'research_data' | 'analysis' | 'report',
  rawContent: any
): AgentOutput => {
  let content = "";

  if (type === 'research_data' && Array.isArray(rawContent)) {
    content = rawContent.join("\n\n");
  }
  else if (type === 'analysis') {
    const item = Array.isArray(rawContent) ? rawContent[0] : rawContent;
    if (typeof item === 'string') {
      const match = item.match(/```json\s*([\s\S]*?)```/);
      const jsonText = match ? match[1] : item;
      try {
        const data = JSON.parse(jsonText.trim());
        content =
          `**Key Insights**\n\n${data.key_insights}\n\n` +
          `**Comparative Analysis**\n\n${data.comparative_analysis}\n\n` +
          `**Narrative**\n\n${data.narrative}`;
      } catch {
        content = item;
      }
    } else {
      content = String(item);
    }
  }
  else if (type === 'report') {
    const item = Array.isArray(rawContent) ? rawContent[0] : rawContent;
    if (typeof item === 'string') {
      const m = item.match(/^content=(['"]?)([\s\S]*)\1/);
      content = m
        ? m[2].replace(/\\n/g, "\n")
        : item;
    } else {
      content = String(item);
    }
    content = content.replace(/^##\s+(.*)$/gm, '**$1**');
  }
  else {
    content = String(rawContent);
  }

  console.log(`Normalized content for [${agent}] (${type}):`, content);
  return { agent, type, content };
};




type AgentCardProps = {
  output: AgentOutput;
  expanded: boolean;
  toggle: () => void;
};

const AgentCard: React.FC<AgentCardProps> = ({ output, expanded, toggle }) => {
  const markdownContent = output?.content || "";
  return (
    <Card sx={{ mb: 2, boxShadow: 2 }}>
      <CardContent sx={{ pb: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center">
            {icons[output.agent] || <FileText size={24} />}
            <Typography variant="h6" fontWeight="bold" sx={{ ml: 1 }}>
              {titles[output.agent]}
            </Typography>
          </Box>
          <IconButton size="small" onClick={toggle} aria-label={expanded ? "Collapse" : "Expand"}>
            {expanded ? <ChevronUp /> : <ChevronDown />}
          </IconButton>
        </Box>
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Box mt={1}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
            >
              {markdownContent}
            </ReactMarkdown>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

const MemoizedAgentCard = React.memo(AgentCard);

export default function Home() {
  const [task, setTask] = useState("");
  const [outputs, setOutputs] = useState<AgentOutput[]>([]);
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [documentText, setDocumentText] = useState("");
  const [addDocStatus, setAddDocStatus] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMsg, setSnackbarMsg] = useState("");

  const toggleExpanded = (agent: string) =>
    setExpandedMap(prev => ({ ...prev, [agent]: !prev[agent] }));

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files);
  };

  const handleAddDocument = async (e: FormEvent) => {
    e.preventDefault();
    setAddDocStatus("Uploading...");
    try {
      if (files) {
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
          formData.append("files", files[i]);
        }
        const response = await fetch("http://localhost:8000/upload-files", {
          method: "POST",
          body: formData,
        });
        const result = await response.json();
        setAddDocStatus(result.message);
        setSnackbarMsg(result.message);
        setSnackbarOpen(true);
      } else {
        const response = await fetch("http://localhost:8000/add-documents", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ documents: [documentText] }),
        });
        const result = await response.json();
        setAddDocStatus(result.message);
        setSnackbarMsg(result.message);
        setSnackbarOpen(true);
      }
    } catch {
      setAddDocStatus("Upload failed.");
      setSnackbarMsg("Upload failed.");
      setSnackbarOpen(true);
    } finally {
      setFiles(null);
      setDocumentText("");
      setTimeout(() => setAddDocStatus(""), 3000);
      setTimeout(() => setSnackbarOpen(false), 3000);
    }
  };

const handleSubmit = async (e: FormEvent) => {
  e.preventDefault();
  setIsLoading(true);
  setOutputs([]);
  setExpandedMap({});

  const response = await fetch("http://localhost:8000/generate-report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  });

  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const eventLines = chunk.split("\n\n").filter(line => line.startsWith("event:"));

    for (const line of eventLines) {
      const eventType = line.match(/event: (\w+)/)?.[1];
      const dataString = line.match(/data: (.*)/s)?.[1];

      console.log("EventType:", eventType, "DataString:", dataString);

      if (eventType && dataString) {
        try {
          const data = JSON.parse(dataString);
          if (eventType === "update") {
            const [agent, agentData] = Object.entries(data)[0] as [string, AgentData];
            console.log("Agent:", agent, "AgentData:", agentData);

            const upsertOutput = (newOutput: AgentOutput) => {
              setOutputs(prev => {
                const AGENT_ORDER = ["researcher", "analyst", "report_writer"];
                const filtered = prev.filter(out => out.agent !== newOutput.agent);
                const updated = [...filtered, newOutput];
                return updated.sort((a, b) => AGENT_ORDER.indexOf(a.agent) - AGENT_ORDER.indexOf(b.agent));
              });

              setExpandedMap(prev => ({
                ...prev,
                [newOutput.agent]: true,
              }));
            };

            


            if (agentData.research_data) {
              upsertOutput(normalizeOutput(agent, 'research_data', agentData.research_data));
            } else if (agentData.analysis) {
              upsertOutput(normalizeOutput(agent, 'analysis', agentData.analysis));
            } else if (agentData.report) {
              upsertOutput(normalizeOutput(agent, 'report', agentData.report));
            }
          } else if (eventType === "error") {
            setOutputs(prev => [...prev, {
              agent: 'error',
              type: 'error',
              content: (data as any).error
            }]);
            setSnackbarMsg((data as any).error);
            setSnackbarOpen(true);
          }
        } catch (e) {
          console.error("Failed to parse event data:", e);
        }
      }
    }
  }

  setIsLoading(false);
  setExpandedMap(prev => ({ ...prev, report_writer: true }));
};

  return (
    <>
      <Box sx={{ minHeight: "100vh", bgcolor: "background.default", fontFamily: "sans-serif" }}>
        <AppBar position="static" color="primary">
          <Toolbar>
            <Typography variant="h5" sx={{ flexGrow: 1, textAlign: "center", fontWeight: "bold" }}>
              Multi-Agent AI Research Platform
            </Typography>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Grid container spacing={4} mb={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold" mb={2}>
                    Start a New Research Task
                  </Typography>
                  <form onSubmit={handleSubmit}>
                    <TextField
                      label="Research Task"
                      multiline
                      minRows={5}
                      fullWidth
                      value={task}
                      onChange={(e) => setTask(e.target.value)}
                      placeholder="e.g., Compare the financial outlook for NVIDIA and AMD."
                      variant="outlined"
                      sx={{ mb: 2 }}
                    />
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      disabled={isLoading}
                      fullWidth
                      startIcon={isLoading ? <CircularProgress size={20} /> : <Search />}
                    >
                      {isLoading ? "Researching..." : "Start Research"}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold" mb={2}>
                    Add to Knowledge Base
                  </Typography>
                  <form onSubmit={handleAddDocument}>
                    <Box mb={2}>
                      <Button variant="outlined" component="label" fullWidth startIcon={<Upload />}>
                        {files ? `${files.length} file(s) selected` : "Upload Files (PDF, DOCX, TXT)"}
                        <input type="file" multiple hidden onChange={handleFileChange} />
                      </Button>
                    </Box>
                    <TextField
                      label="Or paste text"
                      multiline
                      minRows={3}
                      fullWidth
                      value={documentText}
                      onChange={(e) => setDocumentText(e.target.value)}
                      placeholder="Paste text here..."
                      variant="outlined"
                      sx={{ mb: 2 }}
                    />
                    <Button type="submit" variant="contained" color="secondary" fullWidth startIcon={<Upload />}>
                      Add to Knowledge Base
                    </Button>
                    {addDocStatus && (
                      <Alert severity="info" sx={{ mt: 2, textAlign: "center" }}>
                        {addDocStatus}
                      </Alert>
                    )}
                  </form>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {isLoading && outputs.length === 0 && (
            <Box textAlign="center" py={8}>
              <CircularProgress size={48} />
              <Typography variant="body1" color="textSecondary" mt={2}>
                Initializing research agents...
              </Typography>
            </Box>
          )}

          <Box>
            {outputs.map((output, idx) => (
              <MemoizedAgentCard
                key={`${output.agent}-${idx}`}
                output={output}
                expanded={!!expandedMap[output.agent]}
                toggle={() => toggleExpanded(output.agent)}
              />
            ))}
          </Box>
        </Container>

        <Snackbar
          open={snackbarOpen}
          autoHideDuration={3000}
          onClose={() => setSnackbarOpen(false)}
          message={snackbarMsg}
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        />
      </Box>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .fade-enter { animation: fadeIn 0.4s ease-in-out; }
      `}</style>
    </>
  );
}
