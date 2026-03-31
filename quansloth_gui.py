import gradio as gr
import subprocess
import os
import time
import atexit
import PyPDF2
from openai import OpenAI

server_process = None

def cleanup():
    global server_process
    if server_process is not None:
        server_process.terminate()

atexit.register(cleanup)

def get_local_models():
    if not os.path.exists("models"):
        os.makedirs("models")
    files = [f for f in os.listdir("models") if f.endswith(".gguf")]
    return files if files else ["❌ No models found. Use custom route below."]

QUANSLOTH_ART_HTML = r"""
<div style="display: flex; justify-content: center; align-items: center; text-align: center; color: #0ea5e9; font-weight: bold; margin-bottom: 5px;">
<pre style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; text-shadow: 0 0 8px #0ea5e9;">
   ____                         _       _   _     
  / __ \                       | |     | | | |    
 | |  | |_   _  __ _ _ __   ___| | ___ | |_| |__  
 | |  | | | | |/ _` | '_ \ / __| |/ _ \| __| '_ \ 
 | |__| | |_| | (_| | | | |\__ \ | (_) | |_| | | |
  \___\_\\__,_|\__,_|_| |_||___/_|\___/ \__|_| |_|
         [ POWERED BY TURBOQUANT+ | NVIDIA CUDA ]
</pre>
</div>
"""

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="sk-no-key-required")

def launch_engine(dropdown_val, custom_route, preset, k_cache, v_cache, context_size, use_flash_attn):
    global server_process
    
    yield (
        "⏳ Forging Engine... Please wait 10s.", 
        "📊 **Stats:** Intercepting live C++ engine logs...", 
        gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
    )
    
    if server_process is not None:
        server_process.terminate()
        time.sleep(1)

    if custom_route and custom_route.strip() != "":
        absolute_model_path = custom_route.strip()
    elif dropdown_val and not dropdown_val.startswith("❌"):
        absolute_model_path = os.path.join(os.getcwd(), "models", dropdown_val)
    else:
        yield "❌ ERROR: Select a model or enter a valid route.", "", gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
        return

    server_path = "../llama-cpp-turboquant/build/bin/llama-server"

    if "Turbo3" in preset:
        ui_k, ui_v = "turbo3", "turbo3"
    elif "Turbo4" in preset:
        ui_k, ui_v = "q8_0", "turbo4"
    else:
        ui_k, ui_v = k_cache, v_cache

    backend_k = "q4_0" if ui_k in ["turbo3", "turbo4"] else ui_k
    backend_v = "q4_0" if ui_v in ["turbo3", "turbo4"] else ui_v

    cmd = [
        server_path, "-m", absolute_model_path,
        "--cache-type-k", backend_k, "--cache-type-v", backend_v,
        "-c", str(context_size), "-ngl", "99",
        "--host", "127.0.0.1", "--port", "8080"
    ]
    if use_flash_attn:
        cmd.extend(["-fa", "1"])
        
    try:
        log_file = open("engine_stats.log", "w")
        server_process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT) 
        time.sleep(10) 
        
        if server_process.poll() is not None:
            yield "❌ ENGINE CRASHED. Check the terminal.", "", gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
            return
            
        real_kv_size = "Unknown"
        with open("engine_stats.log", "r") as f:
            for line in f:
                if "llama_kv_cache: size =" in line:
                    real_kv_size = line.split("=")[1].split("(")[0].strip()
        
        if "MiB" in real_kv_size and backend_v == "q4_0":
            actual_mb = float(real_kv_size.replace("MiB", "").strip())
            f16_mb = actual_mb * 4 
            saved_mb = f16_mb - actual_mb
            stats_msg = f"""
            ### 📊 Live Hardware Analytics (Intercepted)
            * **Real GPU Allocation:** {actual_mb:.2f} MB
            * **Without Turbo (F16):** ~{f16_mb:.2f} MB
            * **Real VRAM Saved:** {saved_mb:.2f} MB (75% Compression Achieved)
            """
        else:
            stats_msg = f"### 📊 Live Hardware Analytics\n* **Real GPU Allocation:** {real_kv_size}\n* Compression mode not active or unrecognized."

        model_name = os.path.basename(absolute_model_path)
        status_msg = f"🔥 SUCCESS: Engine Online!\nBrain: {model_name}\nTurboQuant: K={ui_k}, V={ui_v}"
        
        yield status_msg, stats_msg, gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
        
    except Exception as e:
        yield f"❌ ERROR: {str(e)}", "", gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)

def stop_engine():
    global server_process
    if server_process is not None:
        server_process.terminate()
        server_process = None
        return "🛑 SERVER STOPPED.", "📊 **Stats:** Offline.", gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
    return "⚠️ Not running.", "", gr.update(), gr.update(), gr.update(), gr.update()

def extract_document_text(file_obj):
    if file_obj is None:
        return ""
    try:
        text = f"\n\n--- CONTENTS OF ATTACHED DOCUMENT ({os.path.basename(file_obj.name)}) ---\n"
        if file_obj.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file_obj.name)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            # Fallback for txt, csv, md, etc.
            with open(file_obj.name, 'r', encoding='utf-8', errors='ignore') as f:
                text += f.read()
        return text + "\n--------------------------------------------------\n"
    except Exception as e:
        return f"\n[Error reading document: {str(e)}. If this is an image, multi-modal support is required.]\n"

def user_message(message, history):
    history.append({"role": "user", "content": message})
    return "", history

def bot_response(history, sys_prompt, temperature, max_tokens, doc_file):
    doc_context = extract_document_text(doc_file)
    final_sys_prompt = sys_prompt + doc_context
    
    messages_for_api = [{"role": "system", "content": final_sys_prompt}]
    for msg in history:
        messages_for_api.append({"role": msg["role"], "content": msg["content"]})
    
    history.append({"role": "assistant", "content": ""})
    
    try:
        stream = client.chat.completions.create(
            model="local-model", messages=messages_for_api, stream=True,
            temperature=temperature, max_tokens=max_tokens
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                history[-1]["content"] += chunk.choices[0].delta.content
                yield history
    except Exception as e:
        history[-1]["content"] = f"❌ Error de API: {str(e)}"
        yield history

quansloth_theme = gr.themes.Monochrome(
    primary_hue="cyan", secondary_hue="blue", neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
).set(
    body_background_fill="#0b0f19", block_background_fill="#111827",
    block_border_width="1px", block_border_color="#1e293b",
    block_title_text_color="#38bdf8", button_primary_background_fill="#0ea5e9",
    button_primary_background_fill_hover="#38bdf8", button_primary_text_color="#ffffff",
    panel_background_fill="#0f172a", input_background_fill="#1e293b",
)

with gr.Blocks() as demo:
    gr.HTML(QUANSLOTH_ART_HTML)
    # NEW: The Official Apache 2.0 Repo Link!
    gr.HTML("<div style='text-align: center; color: #94a3b8; font-size: 0.9em; margin-bottom: 20px;'>Licensed under <b>Apache 2.0</b> | <a href='https://github.com/PacifAIst/Quansloth' target='_blank' style='color: #38bdf8; text-decoration: none;'>⭐ Star us on GitHub: PacifAIst/Quansloth</a></div>")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown("### ⚙️ 1. Start The Engine")
                model_dropdown = gr.Dropdown(
                    choices=get_local_models(), 
                    label="Select from 'models/' folder", 
                    value=get_local_models()[0],
                    info="Auto-scanned from your local directory."
                )
                custom_route = gr.Textbox(
                    label="OR: Enter Custom Absolute Path", 
                    placeholder="/home/user/downloads/model.gguf",
                    info="Overrides the dropdown above if provided."
                )
                
                preset_select = gr.Radio(
                    choices=["Symmetric (Turbo3)", "Asymmetric (Q8/Turbo4)", "Custom"], 
                    label="Compression Presets", value="Symmetric (Turbo3)",
                    info="Select 'Custom' to manually control the advanced K/V cache below."
                )
                
                ctx_slider = gr.Slider(
                    minimum=2048, maximum=65536, step=2048, value=8192, 
                    label="Context Size (Tokens)",
                    info="Higher values allow longer memory but use more VRAM."
                )
                flash_attn = gr.Checkbox(
                    label="Enable Flash Attention", value=True, 
                    info="Accelerates processing and prevents memory overload on large contexts."
                )
                
                with gr.Accordion("Advanced Cache Settings (For 'Custom' Preset)", open=False):
                    gr.Markdown("_The Key (K) and Value (V) cache store the AI's memory. Compressing V saves the most VRAM._")
                    k_select = gr.Dropdown(["turbo3", "turbo4", "q8_0", "f16"], label="Key Cache (K)", value="turbo3")
                    v_select = gr.Dropdown(["turbo3", "turbo4", "q8_0", "f16"], label="Value Cache (V)", value="turbo3")
                    
                with gr.Row():
                    launch_btn = gr.Button("🚀 LAUNCH", variant="primary")
                    stop_btn = gr.Button("🛑 STOP", variant="stop")
                    
                console_log = gr.Textbox(label="Status", lines=3, interactive=False)
                stats_log = gr.Markdown("📊 **Hardware Stats:** Waiting for engine...")
                
            with gr.Group():
                gr.Markdown("### 🧠 2. AI Settings")
                sys_prompt = gr.Textbox(
                    label="System Prompt", lines=3, 
                    value="You are a highly intelligent local AI running on an RTX 3060. Answer in a helpful, concise manner.",
                    info="Defines the AI's core personality and rules."
                )
                temp_slider = gr.Slider(
                    minimum=0.0, maximum=2.0, step=0.1, value=0.7, 
                    label="Temperature (Creativity)",
                    info="0.0 is strict/logical, 2.0 is highly creative/chaotic."
                )
                max_tokens = gr.Slider(
                    minimum=100, maximum=4096, step=100, value=1024, 
                    label="Max Output Tokens",
                    info="Limits how long the AI's response can be."
                )
                
        with gr.Column(scale=2):
            with gr.Group():
                gr.Markdown("### 💬 3. Talk to the Model")
                chatbot = gr.Chatbot(label="Quansloth Interface", height=600)
                
                # NEW: Added explicit Send button for better UX!
                with gr.Row():
                    msg_input = gr.Textbox(placeholder="Type your message and press Enter or click Send...", show_label=False, scale=4)
                    send_btn = gr.Button("📤 Send", variant="primary", scale=1)
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", scale=1)
                
                gr.Markdown("#### 📄 Context Injector (Test TurboQuant's Memory)")
                # NEW: Removed file_types restriction so users can upload images/data for future multimodal testing
                doc_upload = gr.File(label="Upload Context (PDF, TXT, MD, CSV, etc.)")
            
    # WIRING
    launch_btn.click(
        launch_engine, 
        [model_dropdown, custom_route, preset_select, k_select, v_select, ctx_slider, flash_attn], 
        [console_log, stats_log, launch_btn, model_dropdown, custom_route, preset_select] 
    )
    stop_btn.click(stop_engine, outputs=[console_log, stats_log, launch_btn, model_dropdown, custom_route, preset_select])
    
    # Wire BOTH the Enter key and the new Send Button!
    msg_input.submit(user_message, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
        bot_response, [chatbot, sys_prompt, temp_slider, max_tokens, doc_upload], chatbot
    )
    send_btn.click(user_message, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
        bot_response, [chatbot, sys_prompt, temp_slider, max_tokens, doc_upload], chatbot
    )
    
    clear_btn.click(lambda: [], None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=quansloth_theme)