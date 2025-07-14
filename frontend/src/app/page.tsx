"use client";

import React, { useState, FormEvent, ChangeEvent, useRef, useEffect } from "react";
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
  Lightbulb,
  BookOpen,
  Newspaper,
  Sparkles,
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
  Paper,
  MenuItem,
  Stack,
  Divider,
} from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import Skeleton from "@mui/material/Skeleton";
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Chip from '@mui/material/Chip';

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

const agentAccent: Record<string, string> = {
  researcher: '#1976d2',
  analyst: '#43a047',
  report_writer: '#8e24aa',
  error: '#d32f2f',
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
    content = typeof item === 'string' ? item.replace(/\\n/g, '\n') : String(item);
  }
  else if (type === 'report') {
    const item = Array.isArray(rawContent) ? rawContent[0] : rawContent;
    if (typeof item === 'string') {
      const m = item.match(/^content=(["']?)([\s\S]*)\1/);
      content = m
        ? m[2].replace(/\\n/g, "\n")
        : item;
    } else if (item && typeof item === 'object') {
      if (item.error) {
        content = `**Error:** ${item.error}`;
        if (item.raw_output) {
          content += `\n\n**Raw Output:**\n\n${item.raw_output}`;
        }
      } else {
        content = '';
        if (item.key_insights) content += `**Key Insights**\n\n${item.key_insights}\n\n`;
        if (item.comparative_analysis) content += `**Comparative Analysis**\n\n${item.comparative_analysis}\n\n`;
        if (item.narrative) content += `**Narrative**\n\n${item.narrative}\n\n`;
        if (item.conclusion) content += `**Conclusion**\n\n${item.conclusion}\n\n`;
        if (!content) content = JSON.stringify(item, null, 2);
      }
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
  taskType: string;
};

const sectionMap: Record<string, Record<string, { label: string; icon: React.ReactNode }[]>> = {
  market_research: {
    researcher: [
      { label: 'Market Overview', icon: <Lightbulb color="#1976d2" /> },
      { label: 'Competitor Analysis', icon: <Search color="#1976d2" /> },
      { label: 'Key Metrics', icon: <BrainCircuit color="#1976d2" /> },
    ],
    analyst: [
      { label: 'Key Insights', icon: <Lightbulb color="#43a047" /> },
      { label: 'Comparative Analysis', icon: <BookOpen color="#43a047" /> },
      { label: 'Narrative', icon: <Newspaper color="#43a047" /> },
    ],
    report_writer: [
      { label: 'Executive Summary', icon: <Sparkles color="#8e24aa" /> },
      { label: 'Key Findings', icon: <Search color="#8e24aa" /> },
      { label: 'Comparative Analysis', icon: <BrainCircuit color="#8e24aa" /> },
      { label: 'Conclusion', icon: <FileText color="#8e24aa" /> },
    ],
  },
  literature_review: {
    researcher: [
      { label: 'Summary', icon: <BookOpen color="#1976d2" /> },
      { label: 'Key Papers', icon: <Search color="#1976d2" /> },
      { label: 'Trends', icon: <Sparkles color="#1976d2" /> },
    ],
    analyst: [
      { label: 'Key Insights', icon: <Lightbulb color="#43a047" /> },
      { label: 'Comparative Analysis', icon: <BookOpen color="#43a047" /> },
      { label: 'Gaps', icon: <Newspaper color="#43a047" /> },
    ],
    report_writer: [
      { label: 'Executive Summary', icon: <Sparkles color="#8e24aa" /> },
      { label: 'Key Findings', icon: <BookOpen color="#8e24aa" /> },
      { label: 'Trends', icon: <BrainCircuit color="#8e24aa" /> },
      { label: 'Conclusion', icon: <FileText color="#8e24aa" /> },
    ],
  },
  news_aggregation: {
    researcher: [
      { label: 'Top Stories', icon: <Newspaper color="#1976d2" /> },
      { label: 'Trends', icon: <Sparkles color="#1976d2" /> },
    ],
    analyst: [
      { label: 'Sentiment', icon: <Lightbulb color="#43a047" /> },
      { label: 'Key Insights', icon: <BookOpen color="#43a047" /> },
    ],
    report_writer: [
      { label: 'Summary', icon: <Sparkles color="#8e24aa" /> },
      { label: 'Top Stories', icon: <Newspaper color="#8e24aa" /> },
      { label: 'Conclusion', icon: <FileText color="#8e24aa" /> },
    ],
  },
  custom: {
    researcher: [],
    analyst: [],
    report_writer: [],
  },
};

const AgentCard: React.FC<AgentCardProps> = ({ output, expanded, toggle, taskType }) => {
  const markdownContent = output?.content || "";
  const [copied, setCopied] = React.useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(markdownContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };
  const sections = sectionMap[taskType]?.[output.agent] || [];
  // Split content by headings if possible, fallback to markdown
  const splitSections = (content: string) => {
    if (!sections.length) return [{ label: '', icon: null, content }];
    const result: { label: string; icon: React.ReactNode; content: string }[] = [];
    let remaining = content;
    for (let i = 0; i < sections.length; i++) {
      const { label, icon } = sections[i];
      const regex = new RegExp(`(?:^|\n)\s*[#*]*\s*${label}[:\n]*`, 'i');
      const match = remaining.match(regex);
      if (match) {
        const start = match.index! + match[0].length;
        let end = remaining.length;
        for (let j = i + 1; j < sections.length; j++) {
          const nextRegex = new RegExp(`(?:^|\n)\s*[#*]*\s*${sections[j].label}[:\n]*`, 'i');
          const nextMatch = remaining.match(nextRegex);
          if (nextMatch && nextMatch.index! > start) {
            end = nextMatch.index!;
            break;
          }
        }
        result.push({ label, icon, content: remaining.slice(start, end).trim() });
        remaining = remaining.slice(end);
      }
    }
    if (result.length === 0) return [{ label: '', icon: null, content }];
    return result;
  };
  // For Analyst, render full Markdown directly
  if (output.agent === 'analyst') {
    return (
      <Card
        sx={{
          mb: 2,
          boxShadow: 2,
          borderLeft: `6px solid ${agentAccent[output.agent] || '#232326'}`,
          animation: 'fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
        className="fade-in"
      >
        <CardContent sx={{ pb: 1 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Box display="flex" alignItems="center" gap={1}>
              {icons[output.agent] || <FileText size={24} />}
              <Typography variant="h6" fontWeight="bold">
                {titles[output.agent]}
              </Typography>
              <Chip
                label={output.agent.charAt(0).toUpperCase() + output.agent.slice(1)}
                size="small"
                sx={{ ml: 1, bgcolor: agentAccent[output.agent], color: '#fff', fontWeight: 600 }}
              />
            </Box>
            <Box display="flex" alignItems="center" gap={1}>
              <Tooltip title={copied ? "Copied!" : "Copy to clipboard"} arrow>
                <IconButton size="small" onClick={handleCopy} aria-label="Copy output">
                  <ContentCopyIcon fontSize="small" color={copied ? "success" : "inherit"} />
                </IconButton>
              </Tooltip>
              <IconButton size="small" onClick={toggle} aria-label={expanded ? "Collapse" : "Expand"} sx={{ float: 'right', mt: 0 }}>
                {expanded ? <ChevronUp /> : <ChevronDown />}
              </IconButton>
            </Box>
          </Box>
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Box mt={2}>
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
  }
  // For other agents, keep section splitting
  const renderedSections = splitSections(markdownContent);
  return (
    <Card
      sx={{
        mb: 2,
        boxShadow: 2,
        borderLeft: `6px solid ${agentAccent[output.agent] || '#232326'}`,
        animation: 'fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      className="fade-in"
    >
      <CardContent sx={{ pb: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            {icons[output.agent] || <FileText size={24} />}
            <Typography variant="h6" fontWeight="bold">
              {titles[output.agent]}
            </Typography>
            <Chip
              label={output.agent.charAt(0).toUpperCase() + output.agent.slice(1)}
              size="small"
              sx={{ ml: 1, bgcolor: agentAccent[output.agent], color: '#fff', fontWeight: 600 }}
            />
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Tooltip title={copied ? "Copied!" : "Copy to clipboard"} arrow>
              <IconButton size="small" onClick={handleCopy} aria-label="Copy output">
                <ContentCopyIcon fontSize="small" color={copied ? "success" : "inherit"} />
              </IconButton>
            </Tooltip>
            <IconButton size="small" onClick={toggle} aria-label={expanded ? "Collapse" : "Expand"} sx={{ float: 'right', mt: 0 }}>
              {expanded ? <ChevronUp /> : <ChevronDown />}
            </IconButton>
          </Box>
        </Box>
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Box mt={2}>
            {renderedSections.map((section, idx) => (
              <Box key={idx} mb={3}>
                {section.label && (
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    {section.icon}
                    <Typography variant="subtitle1" fontWeight="bold">
                      {section.label}
                    </Typography>
                  </Box>
                )}
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                >
                  {section.content}
                </ReactMarkdown>
              </Box>
            ))}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

const MemoizedAgentCard = React.memo(AgentCard);

const TASK_TYPES = [
  { value: "market_research", label: "Market Research", icon: <Lightbulb color="#1976d2" />, placeholder: "Compare Company A and Company B on recent news and financials." },
  { value: "literature_review", label: "Literature Review", icon: <BookOpen color="#43a047" />, placeholder: "Summarize recent research on quantum computing." },
  { value: "news_aggregation", label: "News Aggregation", icon: <Newspaper color="#fbc02d" />, placeholder: "What are the latest trends in renewable energy?" },
  { value: "custom", label: "Custom Task", icon: <Sparkles color="#8e24aa" />, placeholder: "Describe your custom research or knowledge task." },
];

// Feature flag: show all agent stages or only final report
const showAllAgentStagesDefault = false;

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
  const [taskType, setTaskType] = useState(TASK_TYPES[0].value);
  const [howItWorksOpen, setHowItWorksOpen] = useState(false);
  const agentOutputRef = useRef<HTMLDivElement>(null);
  const errorAlertRef = useRef<HTMLDivElement>(null);
  const [showAllAgentStages, setShowAllAgentStages] = useState(showAllAgentStagesDefault);

  // Get the current task type object for dynamic placeholder/icon
  const currentTaskType = TASK_TYPES.find(t => t.value === taskType) || TASK_TYPES[0];

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
      } else if (documentText.trim().match(/^https?:\/\//i)) {
        const response = await fetch("http://localhost:8000/add-link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: documentText.trim() }),
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
    body: JSON.stringify({ task_description: task }),
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

  // Focus management for agent output
  useEffect(() => {
    if (outputs.length > 0 && agentOutputRef.current) {
      agentOutputRef.current.focus();
    }
  }, [outputs]);

  // Focus management for error alerts
  useEffect(() => {
    if (addDocStatus && (addDocStatus.includes('fail') || addDocStatus.includes('error')) && errorAlertRef.current) {
      errorAlertRef.current.focus();
    }
  }, [addDocStatus]);

  return (
    <>
      {/* Hero/Header Section */}
      <Box sx={{ bgcolor: "background.default", py: { xs: 4, md: 6 }, mb: 4, textAlign: "center", borderRadius: 2 }}>
        <Typography variant="h3" fontWeight="bold" gutterBottom color="text.primary">
          Universal AI Agent Platform
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: "auto" }}>
          Automate research and knowledge workflows with multi-agent AI. Modular, extensible, and ready for any industry.
        </Typography>
        <Button
          variant="outlined"
          color="primary"
          sx={{ mt: 2, borderColor: "divider" }}
          onClick={() => setHowItWorksOpen(true)}
          aria-label="How it works"
        >
          How it works
        </Button>
      </Box>

      {/* Main Form Section */}
      <Container maxWidth="md" sx={{ py: { xs: 2, md: 4 } }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={4} alignItems="stretch">
          {/* Task Card */}
          <Paper elevation={3} sx={{ flex: 1, borderRadius: 4, p: { xs: 2, md: 4 }, minWidth: 320, maxWidth: 480, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <form onSubmit={handleSubmit} style={{ width: '100%' }}>
              <Stack spacing={3}>
                <Typography variant="h5" fontWeight="bold">Start a Task</Typography>
                <Typography color="text.secondary">Select a task type and describe your goal.</Typography>
                <Divider />
                <Tooltip title="Choose what you want the agent to do" arrow>
                  <TextField
                    select
                    label="Task Type"
                    value={taskType}
                    onChange={e => setTaskType(e.target.value)}
                    fullWidth
                    aria-label="Task Type"
                    SelectProps={{
                      IconComponent: () => null,
                      renderValue: (selected) => (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {currentTaskType.icon}
                          <span style={{ color: 'inherit' }}>{TASK_TYPES.find(t => t.value === selected)?.label}</span>
                        </Box>
                      ),
                      MenuProps: {
                        PaperProps: {
                          sx: {
                            bgcolor: 'background.paper',
                            color: 'text.primary',
                            '& .MuiMenuItem-root': {
                              bgcolor: 'background.paper',
                              color: 'text.primary',
                              '&.Mui-selected': { bgcolor: 'action.selected', color: 'text.primary' },
                              '&.Mui-selected:hover': { bgcolor: 'action.hover', color: 'text.primary' },
                              '&:hover': { bgcolor: 'action.hover', color: 'text.primary' },
                            },
                          },
                        },
                      },
                    }}
                    InputProps={{ sx: { bgcolor: 'background.paper', color: 'text.primary', borderRadius: 2, height: 48, border: '1px solid', borderColor: 'divider' } }}
                    InputLabelProps={{ style: { color: "#bdbdbd", fontWeight: 600 } }}
                    sx={{ width: '100%' }}
                  >
                    {TASK_TYPES.map(option => (
                      <MenuItem
                        key={option.value}
                        value={option.value}
                        sx={{
                          bgcolor: 'background.paper',
                          color: 'text.primary',
                          fontWeight: 500,
                          '&.Mui-selected': { bgcolor: 'action.selected', color: 'text.primary' },
                          '&.Mui-selected:hover': { bgcolor: 'action.hover', color: 'text.primary' },
                          '&:hover': { bgcolor: 'action.hover', color: 'text.primary' },
                          transition: 'background 0.15s',
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {option.icon}
                          {option.label}
                        </Box>
                      </MenuItem>
                    ))}
                  </TextField>
                </Tooltip>
                <TextField
                  label="Task Description"
                  value={task}
                  onChange={e => setTask(e.target.value)}
                  fullWidth
                  required
                  placeholder={currentTaskType.placeholder}
                  multiline
                  minRows={3}
                  aria-label="Task Description"
                  InputProps={{ sx: { bgcolor: 'background.paper', color: 'text.primary', borderRadius: 2, minHeight: 80 } }}
                  InputLabelProps={{ style: { color: "#bdbdbd" } }}
                />
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  fullWidth
                  aria-label="Run Agent"
                  startIcon={isLoading ? <CircularProgress size={20} /> : <Search />}
                  disabled={isLoading || !task}
                  sx={{ fontWeight: "bold", borderRadius: 3, fontSize: '1.1rem', py: 2, boxShadow: 1, mt: 1 }}
                >
                  {isLoading ? "Running..." : "Run Agent"}
                </Button>
              </Stack>
            </form>
          </Paper>

          {/* Add to Knowledge Base Card */}
          <Paper elevation={3} sx={{ flex: 1, borderRadius: 4, p: { xs: 2, md: 4 }, minWidth: 320, maxWidth: 480, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <form onSubmit={handleAddDocument} style={{ width: '100%' }}>
              <Typography variant="h5" fontWeight="bold">Add to Knowledge Base</Typography>
              <Typography color="text.secondary">Upload files or paste text to expand your knowledge base.</Typography>
              <Divider />
              <Tooltip title="Upload files (PDF, DOCX, TXT)" arrow>
                <Button variant="outlined" component="label" fullWidth startIcon={<Upload />} aria-label="Upload Files">
                  {files ? `${files.length} file(s) selected` : "Upload Files (PDF, DOCX, TXT)"}
                  <input type="file" multiple hidden onChange={handleFileChange} />
                </Button>
              </Tooltip>
              <TextField
                label="Or paste text"
                multiline
                minRows={3}
                fullWidth
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                placeholder="Paste text here..."
                variant="outlined"
                aria-label="Paste text"
              />
              <Button type="submit" variant="contained" color="secondary" fullWidth startIcon={<Upload />} sx={{ fontWeight: 'bold', borderRadius: 3, fontSize: '1.1rem', py: 2, boxShadow: 1, mt: 1 }} aria-label="Add to Knowledge Base">
                Add to Knowledge Base
              </Button>
              {addDocStatus && (
                <Alert
                  ref={addDocStatus.includes('fail') || addDocStatus.includes('error') ? errorAlertRef : undefined}
                  severity={addDocStatus.includes('fail') || addDocStatus.includes('error') ? "error" : "info"}
                  sx={{ textAlign: "center" }}
                  tabIndex={-1}
                  aria-live="assertive"
                  aria-label={addDocStatus.includes('fail') || addDocStatus.includes('error') ? "Error alert" : "Info alert"}
                >
                  {addDocStatus}
                </Alert>
              )}
            </form>
          </Paper>
        </Stack>
      </Container>

      {/* Agent Output Section - Empty State & Error Handling */}
      <Box sx={{ mt: 6, mb: 4 }}>
        <Box display="flex" alignItems="center" justifyContent="flex-end" mb={2}>
          <Button
            variant="outlined"
            size="small"
            onClick={() => setShowAllAgentStages((v) => !v)}
            sx={{ textTransform: 'none', borderRadius: 2 }}
          >
            {showAllAgentStages ? 'Show Only Final Report' : 'Show All Steps'}
          </Button>
        </Box>
        {outputs.length === 0 && isLoading ? (
          <Box>
            {(showAllAgentStages ? [0, 1, 2] : [0]).map((i) => (
              <Card key={i} sx={{ mb: 2, boxShadow: 2, borderLeft: '6px solid #333' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={1}>
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="text" width={120} height={28} />
                  </Box>
                  <Skeleton variant="rectangular" height={60} sx={{ mb: 1, borderRadius: 2 }} />
                  <Skeleton variant="rectangular" height={32} sx={{ mb: 1, borderRadius: 2 }} />
                </CardContent>
              </Card>
            ))}
          </Box>
        ) : outputs.length === 0 && !isLoading ? (
          <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight={120}>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
              No results yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Run a task to see agent results here.
            </Typography>
          </Box>
        ) : (
          <Box
            ref={agentOutputRef}
            tabIndex={-1}
            aria-live="polite"
            aria-label="Agent output results"
            sx={{ outline: 'none' }}
          >
            {(showAllAgentStages
              ? outputs
              : outputs.filter((o) => o.agent === 'report_writer')
            ).map((output, idx) => (
              <MemoizedAgentCard
                key={`${output.agent}-${idx}`}
                output={output}
                expanded={!!expandedMap[output.agent]}
                toggle={() => toggleExpanded(output.agent)}
                taskType={taskType}
              />
            ))}
            {!showAllAgentStages && outputs.some((o) => o.agent !== 'report_writer') && (
              <Box display="flex" justifyContent="center" mt={2}>
                <Button
                  variant="text"
                  size="small"
                  onClick={() => setShowAllAgentStages(true)}
                  sx={{ textTransform: 'none', borderRadius: 2 }}
                >
                  Show Details (Researcher & Analyst Steps)
                </Button>
              </Box>
            )}
          </Box>
        )}
      </Box>

      {/* Feedback Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMsg}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        ContentProps={{ 'aria-live': 'polite' }}
      />

      <Dialog open={howItWorksOpen} onClose={() => setHowItWorksOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Sparkles color="#8e24aa" /> How it works
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            <b>1.</b> Select a <b>Task Type</b> (e.g., Market Research, Literature Review, News Aggregation).
            <br /><b>2.</b> Describe your goal in the <b>Task Description</b> field.
            <br /><b>3.</b> Click <b>Run Agent</b> to launch a multi-agent workflow that plans, retrieves, and synthesizes information from multiple sources.
            <br /><b>4.</b> Results are streamed in real time below.
          </Typography>
          <Typography variant="subtitle2" sx={{ mt: 2 }}>Examples:</Typography>
          <Paper variant="outlined" sx={{ p: 2, mt: 1, bgcolor: "background.paper" }}>
            <ul style={{ margin: 0, paddingLeft: 20, color: "inherit" }}>
              <li><b>Market Research:</b> Compare Company A and Company B on recent news and financials.</li>
              <li><b>Literature Review:</b> Summarize recent research on quantum computing.</li>
              <li><b>News Aggregation:</b> What are the latest trends in renewable energy?</li>
            </ul>
          </Paper>
        </DialogContent>
      </Dialog>

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
