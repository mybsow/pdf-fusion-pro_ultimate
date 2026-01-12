"""
Routes principales pour les outils PDF
"""

import io
import base64
import zipfile
import json
from datetime import datetime
from flask import render_template_string, jsonify, request, Response
from . import pdf_bp
from config import AppConfig
from .engine import PDFEngine
from utils.stats_manager import stats_manager

# ============================================================
# TEMPLATE HTML COMPLET - VERSION CORRIGÉE
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    
    <!-- SEO Meta Description -->
    <meta name="description" content="{{ description }}">
    
    <!-- META ROBOTS -->
    <meta name="robots" content="index, follow">
    
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ config.ADSENSE_PUBLISHER_ID }}" crossorigin="anonymous"></script>
    
    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
    :root {
        --primary-color: #4361ee;
        --primary-dark: #3a0ca3;
        --secondary-color: #4cc9f0;
        --success-color: #2ecc71;
        --warning-color: #f39c12;
        --danger-color: #e74c3c;
        --light-color: #f8f9fa;
        --dark-color: #212529;
        --gray-color: #6c757d;
        --sidebar-width: 280px;
        --border-radius: 12px;
        --shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
        --transition: all 0.3s ease;
    }
    
    [data-bs-theme="dark"] {
        --light-color: #1a1d20;
        --dark-color: #f8f9fa;
        --gray-color: #adb5bd;
        --shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
    }
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: var(--dark-color);
        min-height: 100vh;
        transition: var(--transition);
    }
    
    [data-bs-theme="dark"] body {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }
    
    /* Header */
    .main-header {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        height: 60px;
        display: flex;
        align-items: center;
        padding: 0 1rem;
    }
    
    [data-bs-theme="dark"] .main-header {
        background: rgba(26, 29, 32, 0.95);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .logo {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        color: var(--primary-color);
        text-decoration: none;
        height: 60px;
        display: flex;
        align-items: center;
        flex: 1;
    }
    
    .header-actions {
        display: flex;
        align-items: center;
        gap: 1rem;
        height: 60px;
    }
    
    /* Layout */
    .app-container {
        display: flex;
        min-height: calc(100vh - 60px);
        margin-top: 60px;
    }
    
    /* Sidebar */
    .sidebar {
        width: var(--sidebar-width);
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 0, 0, 0.05);
        position: fixed;
        top: 60px;
        left: 0;
        height: calc(100vh - 60px);
        z-index: 100;
        padding-top: 1rem;
        box-shadow: var(--shadow);
        overflow-y: auto;
        transition: transform 0.3s ease;
    }
    
    [data-bs-theme="dark"] .sidebar {
        background: rgba(26, 29, 32, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .sidebar-nav {
        padding: 1rem;
    }
    
    .sidebar-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: var(--border-radius);
        cursor: pointer;
        transition: var(--transition);
        color: var(--gray-color);
        text-decoration: none;
    }
    
    .sidebar-item:hover {
        background: rgba(67, 97, 238, 0.1);
        color: var(--primary-color);
    }
    
    .sidebar-item.active {
        background: var(--primary-color);
        color: white;
        box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
    }
    
    /* Sidebar de publicité gauche */
    .ads-left-sidebar {
        width: 280px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 0, 0, 0.05);
        position: fixed;
        top: 60px;
        left: var(--sidebar-width);
        height: calc(100vh - 60px);
        padding: 1rem;
        overflow-y: auto;
        box-shadow: var(--shadow);
        z-index: 99;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    [data-bs-theme="dark"] .ads-left-sidebar {
        background: rgba(26, 29, 32, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Main Content */
    .main-content {
        flex: 1;
        margin-left: calc(var(--sidebar-width) + 280px);
        padding: 1rem;
        max-width: calc(100% - var(--sidebar-width) - 280px - 300px);
        transition: var(--transition);
    }
    
    /* Ads Sidebar (Right) */
    .ads-sidebar {
        width: 280px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-left: 1px solid rgba(0, 0, 0, 0.05);
        position: fixed;
        top: 60px;
        right: 0;
        height: calc(100vh - 60px);
        padding: 1rem;
        overflow-y: auto;
        box-shadow: var(--shadow);
        z-index: 99;
        transition: var(--transition);
    }

    [data-bs-theme="dark"] .ads-sidebar {
        background: rgba(26, 29, 32, 0.95);
        border-left: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Responsive design */
    @media (max-width: 1400px) {
        .ads-left-sidebar {
            width: 200px;
        }
        
        .main-content {
            margin-left: calc(var(--sidebar-width) + 200px);
            max-width: calc(100% - var(--sidebar-width) - 200px - 300px);
        }
    }
    
    @media (max-width: 1200px) {
        .ads-left-sidebar {
            width: 150px;
        }
        
        .main-content {
            margin-left: calc(var(--sidebar-width) + 150px);
            max-width: calc(100% - var(--sidebar-width) - 150px - 250px);
        }
        
        .ads-sidebar {
            width: 250px;
        }
    }
    
    @media (max-width: 992px) {
        .ads-left-sidebar {
            display: none;
        }
        
        .main-content {
            margin-left: var(--sidebar-width);
            max-width: calc(100% - var(--sidebar-width) - 250px);
        }
    }
    
    @media (max-width: 768px) {
        .sidebar {
            transform: translateX(-100%);
            width: 100%;
            max-width: 320px;
        }
        
        .sidebar.open {
            transform: translateX(0);
        }
        
        .main-content {
            margin-left: 0 !important;
            max-width: 100% !important;
            padding: 1rem;
        }
        
        .ads-left-sidebar {
            display: none;
        }
        
        .ads-sidebar {
            display: none;
        }
        
        .mobile-menu-toggle {
            display: block;
        }
        
        .header-actions .nav-links {
            display: none;
        }
    }
    
    /* Hero Section */
    .hero-section {
        padding: 2rem 0;
        text-align: center;
        max-width: 800px;
        margin: 0 auto;
    }
    
    .hero-title {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        color: var(--gray-color);
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    /* Tool Container */
    .tool-container {
        background: white;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        overflow: hidden;
        display: none;
        margin-bottom: 2rem;
    }
    
    [data-bs-theme="dark"] .tool-container {
        background: var(--light-color);
    }
    
    .tool-container.active {
        display: block;
    }
    
    .tool-header {
        padding: 2rem 2rem 1rem;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    [data-bs-theme="dark"] .tool-header {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .tool-header h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        margin: 0;
        color: var(--primary-color);
    }
    
    .tool-content {
        padding: 2rem;
    }
    
    /* Upload Zone */
    .upload-zone {
        border: 3px dashed #ddd;
        border-radius: var(--border-radius);
        padding: 3rem 2rem;
        text-align: center;
        cursor: pointer;
        transition: var(--transition);
        background: rgba(248, 249, 250, 0.5);
        margin-bottom: 2rem;
    }
    
    [data-bs-theme="dark"] .upload-zone {
        border-color: #444;
        background: rgba(26, 29, 32, 0.5);
    }
    
    .upload-zone:hover {
        border-color: var(--primary-color);
        background: rgba(67, 97, 238, 0.05);
    }
    
    .upload-zone.drag-over {
        border-color: var(--success-color);
        background: rgba(46, 204, 113, 0.1);
    }
    
    .upload-icon {
        font-size: 3rem;
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    
    /* File List */
    .file-list {
        margin: 1.5rem 0;
    }
    
    .file-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem;
        background: var(--light-color);
        border-radius: 8px;
        margin-bottom: 0.75rem;
        transition: var(--transition);
    }
    
    .file-item:hover {
        transform: translateX(5px);
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
    }
    
    .file-info {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex: 1;
    }
    
    .file-icon {
        color: var(--danger-color);
        font-size: 1.5rem;
    }
    
    .file-details h6 {
        margin: 0;
        font-weight: 600;
    }
    
    .file-details small {
        color: var(--gray-color);
    }
    
    .file-actions {
        display: flex;
        gap: 0.5rem;
    }
    
    /* Buttons */
    .btn {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: var(--transition);
        border: none;
        cursor: pointer;
    }
    
    .btn-primary {
        background: var(--primary-color);
        color: white;
    }
    
    .btn-primary:hover {
        background: var(--primary-dark);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(67, 97, 238, 0.3);
    }
    
    .btn-success {
        background: var(--success-color);
        color: white;
    }
    
    .btn-outline {
        background: transparent;
        border: 2px solid var(--primary-color);
        color: var(--primary-color);
    }
    
    .btn-outline:hover {
        background: var(--primary-color);
        color: white;
    }
    
    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    .action-buttons {
        display: flex;
        gap: 1rem;
        margin-top: 2rem;
        flex-wrap: wrap;
    }
    
    /* Form Controls */
    .form-group {
        margin-bottom: 1.5rem;
    }
    
    .form-control, .form-select {
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        transition: var(--transition);
    }
    
    [data-bs-theme="dark"] .form-control,
    [data-bs-theme="dark"] .form-select {
        background: #2d2d44;
        border-color: #444;
        color: var(--dark-color);
    }
    
    .form-control:focus, .form-select:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 0.25rem rgba(67, 97, 238, 0.25);
    }
    
    /* Preview */
    .preview-container {
        margin-top: 2rem;
        padding: 1.5rem;
        background: var(--light-color);
        border-radius: var(--border-radius);
    }
    
    .preview-title {
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--primary-color);
    }
    
    .preview-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 1rem;
    }
    
    .preview-item {
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        background: white;
    }
    
    .preview-frame {
        width: 100%;
        height: 200px;
        border: none;
    }
    
    .preview-label {
        padding: 0.5rem;
        text-align: center;
        background: var(--light-color);
        font-size: 0.875rem;
        color: var(--gray-color);
    }
    
    /* Footer */
    .main-footer {
        background: rgba(255, 255, 255, 0.95);
        border-top: 1px solid rgba(0, 0, 0, 0.05);
        padding: 2rem 0;
        margin-top: 2rem;
        position: relative;
        z-index: 100;
    }
    
    [data-bs-theme="dark"] .main-footer {
        background: rgba(26, 29, 32, 0.95);
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .footer-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 2rem;
        margin-left: calc(var(--sidebar-width) + 280px);
        padding: 0 1rem;
    }
    
    @media (max-width: 768px) {
        .footer-content {
            margin-left: 0;
            flex-direction: column;
            text-align: center;
        }
    }
    
    .footer-logo {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 1.25rem;
        color: var(--primary-color);
        text-decoration: none;
    }
    
    .footer-links {
        display: flex;
        gap: 1.5rem;
        flex-wrap: wrap;
    }
    
    /* Loader */
    .loader-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 2000;
    }
    
    .loader {
        background: white;
        padding: 2rem;
        border-radius: var(--border-radius);
        text-align: center;
        box-shadow: var(--shadow);
        min-width: 300px;
    }
    
    .spinner {
        width: 50px;
        height: 50px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid var(--primary-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Toast Notifications */
    .toast-container {
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 1000;
        max-width: 350px;
    }
    
    .toast {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        transform: translateX(400px);
        transition: transform 0.3s ease;
    }
    
    .toast.show {
        transform: translateX(0);
    }
    
    .toast-icon {
        font-size: 1.25rem;
    }
    
    .toast-success .toast-icon {
        color: var(--success-color);
    }
    
    .toast-error .toast-icon {
        color: var(--danger-color);
    }
    
    .toast-info .toast-icon {
        color: var(--primary-color);
    }
    
    .toast-content {
        flex: 1;
    }
    
    .toast-title {
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .toast-message {
        color: var(--gray-color);
        font-size: 0.9rem;
    }
    
    .toast-close {
        background: none;
        border: none;
        color: var(--gray-color);
        cursor: pointer;
        padding: 0;
    }
    
    /* Theme Toggle */
    .theme-toggle {
        background: none;
        border: none;
        color: var(--gray-color);
        cursor: pointer;
        font-size: 1.25rem;
        padding: 0.5rem;
        border-radius: 50%;
        transition: var(--transition);
    }
    
    .theme-toggle:hover {
        background: rgba(0, 0, 0, 0.05);
        color: var(--primary-color);
    }
    
    /* Mobile Menu Toggle */
    .mobile-menu-toggle {
        display: none;
        background: none;
        border: none;
        color: var(--gray-color);
        font-size: 1.5rem;
        cursor: pointer;
        margin-right: 1rem;
    }
    
    .ad-label {
        font-size: 0.75rem;
        color: var(--gray-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .ad-sidebar-item {
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: var(--light-color);
        border-radius: var(--border-radius);
    }
    
    /* Stats Widget */
    .stats-widget h6 {
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .stats-widget .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.25rem 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    [data-bs-theme="dark"] .stats-widget .stat-item {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stats-widget .stat-item:last-child {
        border-bottom: none;
    }
    
    .stats-widget .stat-value {
        font-weight: 600;
    }
    
    /* Overlay pour mobile menu */
    .sidebar-overlay {
        display: none;
        position: fixed;
        top: 60px;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 999;
    }
    
    .sidebar-overlay.active {
        display: block;
    }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="main-header">
        <button class="mobile-menu-toggle" id="mobileMenuToggle">
            <i class="fas fa-bars"></i>
        </button>
        
        <a href="/" class="logo">
            <i class="fas fa-file-pdf me-2"></i>{{ config.NAME }}
        </a>
        
        <div class="header-actions">
            <button class="theme-toggle" id="themeToggle">
                <i class="fas fa-moon"></i>
            </button>
        </div>
    </header>

    <!-- Sidebar Overlay pour mobile -->
    <div class="sidebar-overlay" id="sidebarOverlay"></div>

    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-nav">
            <a href="#" class="sidebar-item active" data-tool="merge">
                <i class="fas fa-object-group icon"></i>
                <span class="label">Fusionner PDF</span>
            </a>
            <a href="#" class="sidebar-item" data-tool="split">
                <i class="fas fa-cut icon"></i>
                <span class="label">Diviser PDF</span>
            </a>
            <a href="#" class="sidebar-item" data-tool="rotate">
                <i class="fas fa-sync-alt icon"></i>
                <span class="label">Tourner PDF</span>
            </a>
            <a href="#" class="sidebar-item" data-tool="compress">
                <i class="fas fa-compress-alt icon"></i>
                <span class="label">Compresser PDF</span>
            </a>
        </div>
    </div>

    <!-- Sidebar de publicité gauche -->
    <div class="ads-left-sidebar" id="adsLeftSidebar">
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="1122334455"
                 data-ad-format="vertical"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
        
        <div class="ad-sidebar-item">
            <h6 class="mb-3"><i class="fas fa-bolt me-2"></i>Outils Rapides</h6>
            <div class="small">
                <p class="mb-2">Fusionnez jusqu'à 10 PDFs en un clic</p>
                <p class="mb-2">Divisez par pages ou plages</p>
                <p class="mb-2">Tournez à 90°, 180° ou 270°</p>
                <p class="mb-0">Compressez sans perte de qualité</p>
            </div>
        </div>
        
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="5544332211"
                 data-ad-format="vertical"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Hero Section -->
        <section class="hero-section">
            <h1 class="hero-title">Transformez vos PDFs en toute simplicité</h1>
            <p class="hero-subtitle">
                Outil PDF tout-en-un : fusion, division, rotation et compression. Rapide, sécurisé et 100% gratuit.
                <br>Aucune inscription requise – vos fichiers ne quittent jamais votre navigateur.
            </p>
        </section>

        <!-- Tool Containers -->
        <div class="tool-container active" id="mergeTool">
            <div class="tool-header">
                <h3><i class="fas fa-object-group me-2"></i>Fusionner des fichiers PDF</h3>
                <p class="text-muted mb-0">Combine plusieurs PDF en un seul document organisé</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="mergeUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Glissez-déposez vos fichiers PDF</h4>
                        <p>ou cliquez pour sélectionner (max 10 fichiers, 50MB chacun)</p>
                    </div>
                    <input type="file" id="mergeFileInput" accept=".pdf" multiple style="display: none;">
                </div>
                
                <div class="file-list" id="mergeFileList"></div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processMerge()" id="mergeButton" disabled>
                        <i class="fas fa-magic me-2"></i>Fusionner les PDFs
                    </button>
                    <button class="btn btn-outline" onclick="clearMergeFiles()">
                        <i class="fas fa-trash me-2"></i>Effacer la liste
                    </button>
                </div>
            </div>
        </div>

        <div class="tool-container" id="splitTool">
            <div class="tool-header">
                <h3><i class="fas fa-cut me-2"></i>Diviser un fichier PDF</h3>
                <p class="text-muted mb-0">Extrayez des pages spécifiques ou divisez par plages</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="splitUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Sélectionnez un fichier PDF à diviser</h4>
                        <p>Glissez-déposez ou cliquez pour choisir</p>
                    </div>
                    <input type="file" id="splitFileInput" accept=".pdf" style="display: none;">
                </div>
                
                <div class="file-list" id="splitFileInfo"></div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label">Mode de division</label>
                            <select class="form-select" id="splitMode">
                                <option value="all">Chaque page séparément</option>
                                <option value="range">Plages de pages (ex: 1-3,5-7)</option>
                                <option value="selected">Pages spécifiques (ex: 1,4,8)</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label" id="splitArgLabel">Argument</label>
                            <input type="text" class="form-control" id="splitArg" 
                                   placeholder="Ex: 1-3, 5-7 ou 1,4,8">
                            <small class="text-muted" id="splitHelpText">
                                Laissez vide pour diviser toutes les pages
                            </small>
                        </div>
                    </div>
                </div>
                
                <div class="preview-container" id="splitPreview" style="display: none;">
                    <h5 class="preview-title"><i class="fas fa-eye me-2"></i>Aperçu des pages</h5>
                    <div class="preview-grid" id="splitPreviewGrid"></div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processSplit()" id="splitButton" disabled>
                        <i class="fas fa-cut me-2"></i>Diviser le PDF
                    </button>
                    <button class="btn btn-success" onclick="processSplitZip()" id="splitZipButton" disabled>
                        <i class="fas fa-file-archive me-2"></i>Télécharger en ZIP
                    </button>
                    <button class="btn btn-outline" onclick="generatePreview()" id="previewButton" disabled>
                        <i class="fas fa-eye me-2"></i>Aperçu
                    </button>
                </div>
            </div>
        </div>

        <div class="tool-container" id="rotateTool">
            <div class="tool-header">
                <h3><i class="fas fa-sync-alt me-2"></i>Tourner un fichier PDF</h3>
                <p class="text-muted mb-0">Faites pivoter des pages spécifiques ou l'ensemble du document</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="rotateUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Sélectionnez un fichier PDF à tourner</h4>
                        <p>Glissez-déposez ou cliquez pour choisir</p>
                    </div>
                    <input type="file" id="rotateFileInput" accept=".pdf" style="display: none;">
                </div>
                
                <div class="file-list" id="rotateFileInfo"></div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label">Pages à tourner</label>
                            <input type="text" class="form-control" id="rotatePages" 
                                   placeholder="Ex: 1,3-5 ou laissez 'all' pour toutes">
                            <small class="text-muted">
                                Format: numéros séparés par des virgules, plages avec tiret
                            </small>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label">Angle de rotation</label>
                            <select class="form-select" id="rotateAngle">
                                <option value="90">90° (Sens horaire)</option>
                                <option value="180">180° (Demi-tour)</option>
                                <option value="270">270° (Sens anti-horaire)</option>
                                <option value="-90">-90° (Sens anti-horaire)</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processRotate()" id="rotateButton" disabled>
                        <i class="fas fa-sync-alt me-2"></i>Tourner le PDF
                    </button>
                    <button class="btn btn-outline" onclick="resetRotateForm()">
                        <i class="fas fa-redo me-2"></i>Réinitialiser
                    </button>
                </div>
            </div>
        </div>

        <div class="tool-container" id="compressTool">
            <div class="tool-header">
                <h3><i class="fas fa-compress-alt me-2"></i>Compresser un fichier PDF</h3>
                <p class="text-muted mb-0">Réduisez la taille de vos PDFs sans perte de qualité notable</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="compressUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Sélectionnez un fichier PDF à compresser</h4>
                        <p>Glissez-déposez ou cliquez pour choisir</p>
                    </div>
                    <input type="file" id="compressFileInput" accept=".pdf" style="display: none;">
                </div>
                
                <div class="file-list" id="compressFileInfo"></div>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    La compression réduit la taille du fichier en optimisant les images et en supprimant les métadonnées inutiles.
                    La qualité visuelle reste excellente pour la plupart des usages.
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processCompress()" id="compressButton" disabled>
                        <i class="fas fa-compress-alt me-2"></i>Compresser le PDF
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Ads Sidebar (Right) -->
    <div class="ads-sidebar">
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="9876543210"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
        
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="8765432109"
                 data-ad-format="vertical"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
        
        <!-- Stats Widget -->
        <div class="ad-sidebar-item stats-widget">
            <h6 class="mb-3"><i class="fas fa-chart-line me-2"></i>Statistiques en direct</h6>
            <div class="small">
                <div class="stat-item">
                    <span><i class="fas fa-file-pdf me-1"></i>Opérations totales:</span>
                    <span id="totalOps" class="stat-value text-primary">0</span>
                </div>
                <div class="stat-item">
                    <span><i class="fas fa-object-group me-1"></i>Fusions:</span>
                    <span id="mergeCount" class="stat-value">0</span>
                </div>
                <div class="stat-item">
                    <span><i class="fas fa-cut me-1"></i>Divisions:</span>
                    <span id="splitCount" class="stat-value text-success">0</span>
                </div>
                <div class="stat-item">
                    <span><i class="fas fa-sync-alt me-1"></i>Rotations:</span>
                    <span id="rotateCount" class="stat-value text-warning">0</span>
                </div>
                <div class="stat-item">
                    <span><i class="fas fa-compress-alt me-1"></i>Compressions:</span>
                    <span id="compressCount" class="stat-value text-info">0</span>
                </div>
            </div>
            <div class="mt-3 pt-2 border-top">
                <button class="btn btn-sm btn-outline-primary w-100" onclick="loadStats()">
                    <i class="fas fa-redo me-1"></i>Actualiser
                </button>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="main-footer">
        <div class="container-fluid">
            <div class="footer-content">
                <a href="/" class="footer-logo">
                    <i class="fas fa-file-pdf me-2"></i>{{ config.NAME }}
                </a>
                
                <div class="footer-info">
                    <div>© {{ current_year }} {{ config.NAME }} • Version {{ config.VERSION }}</div>
                    <div class="mt-1">Développé par <strong>{{ config.DEVELOPER_NAME }}</strong></div>
                    <div class="mt-1">Hébergé sur <strong>{{ config.HOSTING }}</strong> • {{ config.DOMAIN }}</div>
                </div>
                
                <div class="footer-links">
                    <a href="/mentions-legales">Mentions légales</a>
                    <a href="/politique-confidentialite">Confidentialité</a>
                    <a href="/conditions-utilisation">Conditions</a>
                    <a href="/contact">Contact</a>
                    <a href="/a-propos">À propos</a>
                </div>
            </div>
        </div>
    </footer>

    <!-- Loader Overlay -->
    <div class="loader-overlay" id="loaderOverlay">
        <div class="loader">
            <div class="spinner"></div>
            <h4>Traitement en cours</h4>
            <p class="text-muted" id="loaderMessage">Veuillez patienter...</p>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Configuration
        const CONFIG = {
            APP_NAME: "{{ config.NAME }}",
            VERSION: "{{ config.VERSION }}"
        };

        // State Management
        let state = {
            activeTool: 'merge',
            files: {
                merge: [],
                split: null,
                rotate: null,
                compress: null
            }
        };

        // DOM Elements
        const elements = {
            sidebarItems: document.querySelectorAll('.sidebar-item'),
            toolContainers: document.querySelectorAll('.tool-container'),
            themeToggle: document.getElementById('themeToggle'),
            mobileMenuToggle: document.getElementById('mobileMenuToggle'),
            sidebar: document.getElementById('sidebar'),
            sidebarOverlay: document.getElementById('sidebarOverlay'),
            loaderOverlay: document.getElementById('loaderOverlay'),
            loaderMessage: document.getElementById('loaderMessage'),
            toastContainer: document.getElementById('toastContainer'),
            stats: {
                totalOps: document.getElementById('totalOps'),
                mergeCount: document.getElementById('mergeCount'),
                splitCount: document.getElementById('splitCount'),
                rotateCount: document.getElementById('rotateCount'),
                compressCount: document.getElementById('compressCount')
            }
        };

        // Initialize Application
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Initializing application...');
            initTheme();
            initSidebar();
            initFileUploads();
            initToolSwitching();
            initSplitMode();
            loadStats();
            initAdSense();
            
            // Log pour débogage
            console.log('Application initialized');
            console.log('Theme toggle exists:', !!elements.themeToggle);
            console.log('Mobile menu toggle exists:', !!elements.mobileMenuToggle);
            console.log('Sidebar items:', elements.sidebarItems.length);
        });

        // Theme Management
        function initTheme() {
            console.log('Initializing theme...');
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
            updateThemeIcon(savedTheme);
            
            if (elements.themeToggle) {
                elements.themeToggle.addEventListener('click', function(e) {
                    console.log('Theme toggle clicked');
                    toggleTheme();
                });
            } else {
                console.error('Theme toggle element not found!');
            }
        }

        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            console.log('Switching theme from', currentTheme, 'to', newTheme);
            
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        }

        function updateThemeIcon(theme) {
            if (elements.themeToggle) {
                const icon = elements.themeToggle.querySelector('i');
                if (icon) {
                    icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
                }
            }
        }

        // Sidebar Management
        function initSidebar() {
            console.log('Initializing sidebar...');
            
            // Mobile menu toggle
            if (elements.mobileMenuToggle) {
                elements.mobileMenuToggle.addEventListener('click', function() {
                    console.log('Mobile menu toggle clicked');
                    toggleMobileMenu();
                });
            }
            
            // Close sidebar when clicking overlay
            if (elements.sidebarOverlay) {
                elements.sidebarOverlay.addEventListener('click', function() {
                    closeMobileMenu();
                });
            }
        }

        function toggleMobileMenu() {
            elements.sidebar.classList.toggle('open');
            elements.sidebarOverlay.classList.toggle('active');
        }

        function closeMobileMenu() {
            elements.sidebar.classList.remove('open');
            elements.sidebarOverlay.classList.remove('active');
        }

        // Tool Switching
        function initToolSwitching() {
            console.log('Initializing tool switching...');
            
            elements.sidebarItems.forEach(item => {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    const tool = this.getAttribute('data-tool');
                    console.log('Switching to tool:', tool);
                    switchTool(tool);
                });
            });
        }

        function switchTool(tool) {
            // Update active sidebar item
            elements.sidebarItems.forEach(item => {
                item.classList.remove('active');
                if (item.getAttribute('data-tool') === tool) {
                    item.classList.add('active');
                }
            });

            // Update active container
            elements.toolContainers.forEach(container => {
                container.classList.remove('active');
                if (container.id === tool + 'Tool') {
                    container.classList.add('active');
                }
            });

            state.activeTool = tool;
            
            // Close mobile menu on mobile
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
        }

        // File Upload Management
        function initFileUploads() {
            console.log('Initializing file uploads...');
            
            // Initialize all upload zones
            ['merge', 'split', 'rotate', 'compress'].forEach(tool => {
                initUploadZone(tool);
            });
        }

        function initUploadZone(tool) {
            const zone = document.getElementById(tool + 'UploadZone');
            const input = document.getElementById(tool + 'FileInput');
            
            if (!zone || !input) {
                console.log('Upload zone not found for:', tool);
                return;
            }

            // Click handler
            zone.addEventListener('click', function() {
                input.click();
            });

            // File input change handler
            input.addEventListener('change', function(e) {
                handleFileSelect(tool, e.target.files);
            });

            // Drag and drop handlers
            zone.addEventListener('dragover', function(e) {
                e.preventDefault();
                zone.classList.add('drag-over');
            });

            zone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                zone.classList.remove('drag-over');
            });

            zone.addEventListener('drop', function(e) {
                e.preventDefault();
                zone.classList.remove('drag-over');
                handleFileSelect(tool, e.dataTransfer.files);
            });
        }

        function handleFileSelect(tool, files) {
            if (!files || files.length === 0) return;

            if (tool === 'merge') {
                // Multiple files for merge
                const newFiles = Array.from(files).filter(file => 
                    file.type === 'application/pdf' && file.size <= 50 * 1024 * 1024
                );
                
                if (newFiles.length === 0) {
                    showToast('error', 'Format invalide', 'Seuls les fichiers PDF de moins de 50MB sont acceptés.');
                    return;
                }

                state.files[tool] = state.files[tool].concat(newFiles);
                if (state.files[tool].length > 10) {
                    state.files[tool] = state.files[tool].slice(0, 10);
                    showToast('warning', 'Limite atteinte', 'Maximum 10 fichiers autorisés.');
                }

                updateFileList(tool);
                updateMergeButton();
            } else {
                // Single file for other tools
                const file = files[0];
                
                if (file.type !== 'application/pdf') {
                    showToast('error', 'Format invalide', 'Veuillez sélectionner un fichier PDF.');
                    return;
                }

                if (file.size > 50 * 1024 * 1024) {
                    showToast('error', 'Fichier trop volumineux', 'La taille maximale est de 50MB.');
                    return;
                }

                state.files[tool] = file;
                updateFileInfo(tool);
                updateToolButton(tool);
                
                if (tool === 'split') {
                    document.getElementById('previewButton').disabled = false;
                }
            }
        }

        function updateFileList(tool) {
            const container = document.getElementById(tool + 'FileList');
            if (!container) return;

            if (state.files[tool].length === 0) {
                container.innerHTML = '';
                return;
            }

            container.innerHTML = state.files[tool].map((file, index) => `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-icon">
                            <i class="fas fa-file-pdf"></i>
                        </div>
                        <div class="file-details">
                            <h6>${escapeHtml(file.name)}</h6>
                            <small>${formatFileSize(file.size)}</small>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline" onclick="removeFile('${tool}', ${index})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }

        function updateFileInfo(tool) {
            const container = document.getElementById(tool + 'FileInfo');
            if (!container || !state.files[tool]) {
                container.innerHTML = '';
                return;
            }

            const file = state.files[tool];
            container.innerHTML = `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-icon">
                            <i class="fas fa-file-pdf"></i>
                        </div>
                        <div class="file-details">
                            <h6>${escapeHtml(file.name)}</h6>
                            <small>${formatFileSize(file.size)}</small>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline" onclick="clearFile('${tool}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
        }

        function removeFile(tool, index) {
            state.files[tool].splice(index, 1);
            updateFileList(tool);
            updateMergeButton();
        }

        function clearFile(tool) {
            state.files[tool] = tool === 'merge' ? [] : null;
            if (tool === 'merge') {
                updateFileList(tool);
                updateMergeButton();
            } else {
                updateFileInfo(tool);
                updateToolButton(tool);
                if (tool === 'split') {
                    hideSplitPreview();
                    document.getElementById('previewButton').disabled = true;
                }
            }
        }

        function clearMergeFiles() {
            state.files.merge = [];
            updateFileList('merge');
            updateMergeButton();
        }

        function resetRotateForm() {
            document.getElementById('rotatePages').value = '';
            document.getElementById('rotateAngle').value = '90';
            clearFile('rotate');
        }

        // Button States
        function updateMergeButton() {
            const button = document.getElementById('mergeButton');
            button.disabled = state.files.merge.length === 0;
        }

        function updateToolButton(tool) {
            const button = document.getElementById(tool + 'Button');
            if (button) {
                button.disabled = !state.files[tool];
            }
            
            if (tool === 'split') {
                const zipButton = document.getElementById('splitZipButton');
                if (zipButton) {
                    zipButton.disabled = !state.files[tool];
                }
            }
        }

        // Split Mode Handling
        function initSplitMode() {
            const splitModeSelect = document.getElementById('splitMode');
            if (splitModeSelect) {
                splitModeSelect.addEventListener('change', updateSplitMode);
                updateSplitMode(); // Initial update
            }
        }

        function updateSplitMode() {
            const mode = document.getElementById('splitMode').value;
            const argLabel = document.getElementById('splitArgLabel');
            const argInput = document.getElementById('splitArg');
            const helpText = document.getElementById('splitHelpText');

            switch (mode) {
                case 'all':
                    argLabel.textContent = 'Argument (optionnel)';
                    argInput.placeholder = 'Laissez vide pour toutes les pages';
                    helpText.textContent = 'Laissez vide pour diviser toutes les pages';
                    break;
                case 'range':
                    argLabel.textContent = 'Plages de pages';
                    argInput.placeholder = 'Ex: 1-3, 5-7, 10-12';
                    helpText.textContent = 'Séparez les plages par des virgules (ex: 1-3,5-7)';
                    break;
                case 'selected':
                    argLabel.textContent = 'Pages spécifiques';
                    argInput.placeholder = 'Ex: 1, 4, 8, 12';
                    helpText.textContent = 'Séparez les numéros de page par des virgules';
                    break;
            }
        }

        // Stats Management
        async function loadStats() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                // Update stats display
                if (elements.stats.totalOps) {
                    elements.stats.totalOps.textContent = data.total_operations || '0';
                }
                if (elements.stats.mergeCount) {
                    elements.stats.mergeCount.textContent = data.merges || '0';
                }
                if (elements.stats.splitCount) {
                    elements.stats.splitCount.textContent = data.splits || '0';
                }
                if (elements.stats.rotateCount) {
                    elements.stats.rotateCount.textContent = data.rotations || '0';
                }
                if (elements.stats.compressCount) {
                    elements.stats.compressCount.textContent = data.compressions || '0';
                }
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }

        // Preview Generation
        async function generatePreview() {
            if (!state.files.split) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Génération de l\\'aperçu...'); // CORRIGÉ: apostrophe échappée

            try {
                const base64 = await fileToBase64(state.files.split);
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 }
                    })
                });

                const result = await response.json();

                if (result.success) {
                    displayPreview(result.previews, result.total_pages);
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la génération de l\\'aperçu'); // CORRIGÉ
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de générer l\\'aperçu'); // CORRIGÉ
                console.error('Preview error:', error);
            } finally {
                hideLoader();
            }
        }

        function displayPreview(previews, totalPages) {
            const container = document.getElementById('splitPreview');
            const grid = document.getElementById('splitPreviewGrid');

            if (!previews || previews.length === 0) {
                container.style.display = 'none';
                return;
            }

            grid.innerHTML = previews.map((preview, index) => `
                <div class="preview-item">
                    <iframe class="preview-frame" 
                            src="data:application/pdf;base64,${preview}">
                    </iframe>
                    <div class="preview-label">Page ${index + 1} / ${totalPages}</div>
                </div>
            `).join('');

            container.style.display = 'block';
        }

        function hideSplitPreview() {
            const container = document.getElementById('splitPreview');
            container.style.display = 'none';
        }

        // File Processing Functions
        async function processMerge() {
            if (state.files.merge.length === 0) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner au moins un fichier PDF.');
                return;
            }

            showLoader('Fusion des fichiers PDF...');

            try {
                const filesData = await Promise.all(
                    state.files.merge.map(async file => ({
                        data: await fileToBase64(file)
                    }))
                );

                const response = await fetch('/api/merge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ files: filesData })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/pdf');
                    showToast('success', 'Succès', result.pages + ' pages fusionnées avec succès');
                    loadStats();
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la fusion');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de fusionner les fichiers');
                console.error('Merge error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processSplit() {
            if (!state.files.split) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Division du fichier PDF...');

            try {
                const base64 = await fileToBase64(state.files.split);
                const mode = document.getElementById('splitMode').value;
                const arg = document.getElementById('splitArg').value;

                const response = await fetch('/api/split', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 },
                        mode: mode,
                        arg: arg
                    })
                });

                const result = await response.json();

                if (result.success) {
                    if (result.files.length === 0) {
                        showToast('warning', 'Aucun résultat', 'Aucune page ne correspond aux critères de division');
                    } else {
                        result.files.forEach(file => {
                            downloadFile(file.data, file.filename, 'application/pdf');
                        });
                        showToast('success', 'Succès', result.count + ' fichiers générés avec succès');
                        loadStats();
                    }
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la division');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de diviser le fichier');
                console.error('Split error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processSplitZip() {
            if (!state.files.split) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Création de l\\'archive ZIP...'); // CORRIGÉ

            try {
                const base64 = await fileToBase64(state.files.split);
                const mode = document.getElementById('splitMode').value;
                const arg = document.getElementById('splitArg').value;

                const response = await fetch('/api/split_zip', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 },
                        mode: mode,
                        arg: arg
                    })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/zip');
                    showToast('success', 'Succès', 'Archive ZIP avec ' + result.count + ' fichiers créée');
                    loadStats();
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la création du ZIP');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de créer l\\'archive ZIP'); // CORRIGÉ
                console.error('Split ZIP error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processRotate() {
            if (!state.files.rotate) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            const pages = document.getElementById('rotatePages').value.trim() || 'all';
            const angle = document.getElementById('rotateAngle').value;

            if (pages !== 'all' && !/^[\\d,\\-\\s]+$/.test(pages)) {
                showToast('error', 'Format invalide', 'Format des pages invalide. Utilisez: all, 1,3-5, ou 1,4,8');
                return;
            }

            showLoader('Rotation des pages PDF...');

            try {
                const base64 = await fileToBase64(state.files.rotate);

                const response = await fetch('/api/rotate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 },
                        pages: pages,
                        angle: parseInt(angle)
                    })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/pdf');
                    showToast('success', 'Succès', result.rotated + ' pages tournées sur ' + result.pages + ' totales');
                    loadStats();
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la rotation');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de tourner le fichier');
                console.error('Rotate error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processCompress() {
            if (!state.files.compress) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Compression du fichier PDF...');

            try {
                const base64 = await fileToBase64(state.files.compress);

                const response = await fetch('/api/compress', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 }
                    })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/pdf');
                    showToast('success', 'Succès', 'Fichier compressé avec ' + result.pages + ' pages');
                    loadStats();
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la compression');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de compresser le fichier');
                console.error('Compress error:', error);
            } finally {
                hideLoader();
            }
        }

        // Utility Functions
        function fileToBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => {
                    const base64 = reader.result.split(',')[1];
                    resolve(base64);
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        }

        function downloadFile(base64, filename, mimeType) {
            const link = document.createElement('a');
            link.href = `data:${mimeType};base64,${base64}`;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // UI Helpers
        function showLoader(message = 'Traitement en cours...') {
            elements.loaderMessage.textContent = message;
            elements.loaderOverlay.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }

        function hideLoader() {
            elements.loaderOverlay.style.display = 'none';
            document.body.style.overflow = '';
        }

        function showToast(type, title, message) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            
            const icons = {
                success: 'fas fa-check-circle',
                error: 'fas fa-exclamation-circle',
                warning: 'fas fa-exclamation-triangle',
                info: 'fas fa-info-circle'
            };

            toast.innerHTML = `
                <div class="toast-icon">
                    <i class="${icons[type]}"></i>
                </div>
                <div class="toast-content">
                    <div class="toast-title">${escapeHtml(title)}</div>
                    <div class="toast-message">${escapeHtml(message)}</div>
                </div>
                <button class="toast-close" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;

            elements.toastContainer.appendChild(toast);

            // Animate in
            setTimeout(() => toast.classList.add('show'), 10);

            // Auto remove after 5 seconds
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 5000);
        }

        // AdSense initialization
        function initAdSense() {
            // Initialize ads after a short delay
            setTimeout(() => {
                try {
                    const ads = document.querySelectorAll('.adsbygoogle');
                    ads.forEach(ad => {
                        if (!ad.getAttribute('data-adsbygoogle-status')) {
                            (adsbygoogle = window.adsbygoogle || []).push({});
                        }
                    });
                } catch (e) {
                    console.log('AdSense error:', e);
                }
            }, 1000);
        }

        // Make ALL functions available globally - CORRIGÉ
        window.removeFile = removeFile;
        window.clearFile = clearFile;
        window.clearMergeFiles = clearMergeFiles;
        window.processMerge = processMerge;
        window.processSplit = processSplit;
        window.processSplitZip = processSplitZip;
        window.processRotate = processRotate;
        window.processCompress = processCompress;
        window.generatePreview = generatePreview;
        window.resetRotateForm = resetRotateForm;
        window.loadStats = loadStats;
        window.toggleTheme = toggleTheme;

        console.log('All functions initialized');
    </script>
</body>
</html>
"""

# ============================================================
# ROUTES (inchangées)
# ============================================================

@pdf_bp.route('/')
def home():
    """Page d'accueil principale"""
    return render_template_string(
        HTML_TEMPLATE,
        title="PDF Fusion Pro – Fusionner, Diviser, Tourner, Compresser PDF Gratuit",
        description="Outil PDF en ligne 100% gratuit. Fusionnez plusieurs PDFs en un seul, divisez des PDFs par pages, tournez des pages PDF et compressez des fichiers PDF sans perte de qualité. Aucune inscription requise, traitement sécurisé dans votre navigateur.",
        config=AppConfig,
        current_year=datetime.now().year,
        datetime=datetime,
         rating_html=get_rating_html()  # AJOUTEZ CETTE LIGNE
    )

@pdf_bp.route('/fusion-pdf')
def fusion_pdf():
    """Page dédiée à la fusion PDF"""
    return render_template_string(
        HTML_TEMPLATE,
        title="Fusionner PDF - Outil gratuit pour combiner des fichiers PDF",
        description="Fusionnez gratuitement plusieurs fichiers PDF en un seul document organisé. Interface intuitive, rapide et sécurisée. Aucune inscription requise.",
        config=AppConfig,
        current_year=datetime.now().year,
        datetime=datetime,
         rating_html=get_rating_html()  # AJOUTEZ CETTE LIGNE
    )

@pdf_bp.route('/division-pdf')
def division_pdf():
    """Page dédiée à la division PDF"""
    return render_template_string(
        HTML_TEMPLATE,
        title="Diviser PDF - Extraire des pages de fichiers PDF",
        description="Divisez vos fichiers PDF par pages ou plages spécifiques. Téléchargez les pages séparément ou en archive ZIP. Simple et efficace.",
        config=AppConfig,
        current_year=datetime.now().year,
        datetime=datetime,
         rating_html=get_rating_html()  # AJOUTEZ CETTE LIGNE
    )

@pdf_bp.route('/rotation-pdf')
def rotation_pdf():
    """Page dédiée à la rotation PDF"""
    return render_template_string(
        HTML_TEMPLATE,
        title="Tourner PDF - Corriger l'orientation des pages PDF",
        description="Tournez les pages de vos PDFs à 90°, 180° ou 270°. Corrigez l'orientation de documents scannés facilement.",
        config=AppConfig,
        current_year=datetime.now().year,
        datetime=datetime,
         rating_html=get_rating_html()  # AJOUTEZ CETTE LIGNE
    )

@pdf_bp.route('/compression-pdf')
def compression_pdf():
    """Page dédiée à la compression PDF"""
    return render_template_string(
        HTML_TEMPLATE,
        title="Compresser PDF - Réduire la taille des fichiers PDF",
        description="Compressez vos fichiers PDF pour réduire leur taille sans perte de qualité notable. Optimisez l'espace de stockage et le partage.",
        config=AppConfig,
        current_year=datetime.now().year,
        datetime=datetime,
         rating_html=get_rating_html()  # AJOUTEZ CETTE LIGNE
    )

# ============================================================
# API ENDPOINTS (inchangés)
# ============================================================

@pdf_bp.route('/api/merge', methods=["POST"])
def api_merge():
    """API pour fusionner des PDFs"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "files" not in data:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        files_b64 = data["files"]
        if not isinstance(files_b64, list):
            return jsonify({"error": "Format de fichiers invalide"}), 400
        
        # Décodage des PDFs
        pdfs = []
        for file_data in files_b64:
            if "data" in file_data:
                try:
                    pdfs.append(base64.b64decode(file_data["data"]))
                except (base64.binascii.Error, TypeError):
                    return jsonify({"error": "Format Base64 invalide"}), 400
        
        if not pdfs:
            return jsonify({"error": "Aucun PDF valide fourni"}), 400
        
        # Fusion
        merged_pdf, page_count = PDFEngine.merge(pdfs)
        stats_manager.increment("merges")
        
        return jsonify({
            "success": True,
            "filename": f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(merged_pdf).decode()
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500

@pdf_bp.route('/api/split', methods=["POST"])
def api_split():
    """API pour diviser un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        # Division
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        
        # Préparation des résultats
        result_files = []
        for i, pdf_data in enumerate(split_files):
            result_files.append({
                "filename": f"split_{i+1:03d}.pdf",
                "data": base64.b64encode(pdf_data).decode()
            })
        
        return jsonify({
            "success": True,
            "count": len(split_files),
            "files": result_files
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500

@pdf_bp.route('/api/split_zip', methods=["POST"])
def api_split_zip():
    """API pour diviser un PDF et retourner un ZIP"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        # Division
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        
        # Création du ZIP
        zip_data, zip_name = PDFEngine.create_zip(split_files)
        
        return jsonify({
            "success": True,
            "filename": zip_name,
            "count": len(split_files),
            "data": base64.b64encode(zip_data).decode()
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500

@pdf_bp.route('/api/rotate', methods=["POST"])
def api_rotate():
    """API pour tourner les pages d'un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        angle = int(data.get("angle", 90))
        pages = data.get("pages", "all")
        
        # Rotation
        rotated_pdf, total_pages, rotated_count = PDFEngine.rotate(pdf_bytes, angle, pages)
        stats_manager.increment("rotations")
        
        return jsonify({
            "success": True,
            "filename": f"rotation_{angle}deg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": total_pages,
            "rotated": rotated_count,
            "data": base64.b64encode(rotated_pdf).decode()
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500

@pdf_bp.route('/api/compress', methods=["POST"])
def api_compress():
    """API pour compresser un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        # Compression
        compressed_pdf, page_count = PDFEngine.compress(pdf_bytes)
        stats_manager.increment("compressions")
        
        return jsonify({
            "success": True,
            "filename": f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(compressed_pdf).decode()
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500

@pdf_bp.route('/api/preview', methods=["POST"])
def api_preview():
    """API pour générer des aperçus de PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        # Génération des aperçus
        previews, total_pages = PDFEngine.preview(pdf_bytes)
        stats_manager.increment("previews")
        
        return jsonify({
            "success": True,
            "previews": previews,
            "total_pages": total_pages
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500

@pdf_bp.route('/health')
def health_check():
    """Endpoint de santé de l'application"""
    stats = stats_manager.stats
    return jsonify({
        "status": "healthy",
        "app": AppConfig.NAME,
        "version": AppConfig.VERSION,
        "developer": AppConfig.DEVELOPER_NAME,
        "email": AppConfig.DEVELOPER_EMAIL,
        "hosting": AppConfig.HOSTING,
        "domain": AppConfig.DOMAIN,
        "timestamp": datetime.now().isoformat(),
        "total_operations": stats.get("total_operations", 0),
        "merges": stats.get("merges", 0),
        "splits": stats.get("splits", 0),
        "rotations": stats.get("rotations", 0),
        "compressions": stats.get("compressions", 0),
        "previews": stats.get("previews", 0),
        "user_sessions": stats.get("user_sessions", 0)
    })

@pdf_bp.route('/api/rating', methods=["POST"])
def api_rating():
    """API pour enregistrer les évaluations"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        rating = data.get("rating", 0)
        feedback = data.get("feedback", "")
        
        # Ici, vous pouvez enregistrer l'évaluation dans une base de données
        # Pour l'instant, on simule juste un enregistrement réussi
        print(f"Évaluation reçue: {rating} étoiles - Feedback: {feedback}")
        
        # Enregistrer dans les statistiques
        stats_manager.increment("ratings")
        
        return jsonify({
            "success": True,
            "message": "Évaluation enregistrée",
            "rating": rating
        })
    
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'évaluation: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

def get_rating_html():
    """Génère le HTML pour le système d'évaluation"""
    return '''
    <!-- Système d'évaluation simplifié -->
    <div id="ratingPopup" style="display:none;position:fixed;bottom:20px;right:20px;background:white;border-radius:12px;padding:20px;box-shadow:0 10px 40px rgba(0,0,0,0.15);z-index:9999;width:300px;max-width:90%;">
        <div style="position:relative">
            <button onclick="document.getElementById('ratingPopup').style.display='none'" style="position:absolute;top:5px;right:5px;background:none;border:none;font-size:20px;cursor:pointer;width:30px;height:30px;display:flex;align-items:center;justify-content:center;" aria-label="Fermer">&times;</button>
            <h5 style="margin-bottom:10px;font-size:1.1rem;">Évaluez votre expérience</h5>
            <div style="font-size:24px;margin-bottom:15px">
                <span style="cursor:pointer" onmouseover="highlightStars(1)" onclick="rate(1)" aria-label="1 étoile">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(2)" onclick="rate(2)" aria-label="2 étoiles">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(3)" onclick="rate(3)" aria-label="3 étoiles">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(4)" onclick="rate(4)" aria-label="4 étoiles">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(5)" onclick="rate(5)" aria-label="5 étoiles">☆</span>
            </div>
            <div id="feedbackSection" style="display:none">
                <textarea id="feedback" placeholder="Commentaires (optionnel)" style="width:100%;margin-bottom:10px;padding:8px;border-radius:6px;border:1px solid #ddd;font-size:14px;min-height:60px;" rows="2"></textarea>
                <button onclick="submitRating()" style="background:#4361ee;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;width:100%;font-size:14px;">Envoyer</button>
            </div>
        </div>
    </div>
    
    <div id="ratingTrigger" style="position:fixed;bottom:20px;right:20px;background:#4361ee;color:white;width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:9998;box-shadow:0 4px 12px rgba(67,97,238,0.3);" onclick="showRating()" aria-label="Évaluer l'application">★</div>
    
    <script>
    let selectedRating = 0;
    
    function showRating() {
        document.getElementById("ratingPopup").style.display = "block";
        document.getElementById("ratingTrigger").style.display = "none";
    }
    
    function highlightStars(num) {
        const stars = document.querySelectorAll("#ratingPopup span");
        stars.forEach((star, index) => {
            star.textContent = index < num ? "★" : "☆";
            star.style.color = index < num ? "#ffc107" : "#ccc";
        });
    }
    
    function rate(num) {
        selectedRating = num;
        highlightStars(num);
        document.getElementById("feedbackSection").style.display = "block";
    }
    
    function submitRating() {
        const feedback = document.getElementById("feedback").value;
        fetch("/api/rating", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({rating: selectedRating, feedback: feedback})
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById("ratingPopup").innerHTML = '<div style="text-align:center;padding:20px"><div style="color:green;font-size:40px">✓</div><h5>Merci !</h5><p>Votre évaluation a été enregistrée.</p></div>';
                localStorage.setItem("hasRated", "true");
                setTimeout(() => {
                    document.getElementById("ratingTrigger").style.display = "none";
                }, 3000);
            }
        });
    }
    
    // Afficher après 30s
    setTimeout(() => {
        if (!localStorage.getItem("hasRated")) {
            showRating();
        }
    }, 30000);
    </script>
    '''