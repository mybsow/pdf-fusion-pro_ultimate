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
# TEMPLATE HTML COMPLET
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
    
    <!-- META ROBOTS (SEO OPTIMIZED) -->
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="googlebot" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="bingbot" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    
    <!-- OPEN GRAPH / SOCIAL MEDIA -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ description }}">
    <meta property="og:url" content="https://pdf-fusion-pro-ultimate.onrender.com{{ request.path }}">
    <meta property="og:site_name" content="PDF Fusion Pro">
    <meta property="og:locale" content="fr_FR">
    <meta property="og:image" content="https://pdf-fusion-pro-ultimate.onrender.com/static/og-image.jpg">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="PDF Fusion Pro - Outils PDF gratuits">
    
    <!-- TWITTER CARD -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ title }}">
    <meta name="twitter:description" content="{{ description }}">
    <meta name="twitter:image" content="https://pdf-fusion-pro-ultimate.onrender.com/static/twitter-card.jpg">
    
    <!-- URL CANONIQUE -->
    <link rel="canonical" href="https://pdf-fusion-pro-ultimate.onrender.com{{ request.path if request.path != '/' else '' }}" />
    
    <!-- DONNÉES STRUCTURÉES JSON-LD POUR APPLICATION WEB -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "PDF Fusion Pro",
        "description": "{{ description }}",
        "url": "https://pdf-fusion-pro-ultimate.onrender.com",
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Any",
        "browserRequirements": "Requires JavaScript",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
        },
        "creator": {
            "@type": "Person",
            "name": "{{ config.DEVELOPER_NAME }}",
            "email": "{{ config.DEVELOPER_EMAIL }}"
        },
        "datePublished": "2024-01-01",
        "dateModified": "{{ datetime.now().strftime('%Y-%m-%d') }}",
        "inLanguage": "fr",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": "https://pdf-fusion-pro-ultimate.onrender.com/search?q={search_term_string}"
            },
            "query-input": "required name=search_term_string"
        },
        "featureList": [
            "Fusionner des PDFs",
            "Diviser des PDFs",
            "Tourner des pages PDF",
            "Compresser des PDFs"
        ]
    }
    </script>
    
    <!-- DONNÉES STRUCTURÉES ADDITIONNELLES POUR SITE WEB -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "PDF Fusion Pro",
        "url": "https://pdf-fusion-pro-ultimate.onrender.com",
        "potentialAction": {
            "@type": "SearchAction",
            "target": "https://pdf-fusion-pro-ultimate.onrender.com/search?q={search_term_string}",
            "query-input": "required name=search_term_string"
        },
        "description": "{{ description }}",
        "publisher": {
            "@type": "Person",
            "name": "{{ config.DEVELOPER_NAME }}"
        }
    }
    </script>
    
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ config.ADSENSE_PUBLISHER_ID }}" crossorigin="anonymous"></script>
    <script>
        window.__ads_initialized__ = window.__ads_initialized__ || false;
        if (!window.__ads_initialized__) {
            (adsbygoogle = window.adsbygoogle || []).push({
                google_ad_client: "{{ config.ADSENSE_PUBLISHER_ID }}",
                enable_page_level_ads: true
            });
            window.__ads_initialized__ = true;
        }
    </script>
    
    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Reste du CSS inchangé -->
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
            --sidebar-collapsed: 70px;
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
            min-height: 60px;
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
            margin-left: var(--sidebar-width);
            padding-left: 1rem;
            height: 60px;
            display: flex;
            align-items: center;
        }
        
        .header-actions {
            margin-left: auto;
            padding-right: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            height: 60px;
        }
        
        /* Layout */
        .app-container {
            display: flex;
            min-height: calc(100vh - 60px);
        }
        
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(0, 0, 0, 0.05);
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            z-index: 100;
            transition: var(--transition);
            padding-top: 60px;
            box-shadow: var(--shadow);
        }
        
        [data-bs-theme="dark"] .sidebar {
            background: rgba(26, 29, 32, 0.95);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .sidebar-header {
            padding: 1.5rem;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            display: none;
        }
        
        [data-bs-theme="dark"] .sidebar-header {
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
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
            transform: translateX(5px);
        }
        
        .sidebar-item.active {
            background: var(--primary-color);
            color: white;
            box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
        }
        
        .sidebar-item .icon {
            font-size: 1.25rem;
            min-width: 24px;
        }
        
        .sidebar-item .label {
            font-weight: 500;
            white-space: nowrap;
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
        }
        
        @media (max-width: 1400px) {
            .ads-left-sidebar {
                display: none;
            }
            
            .main-content {
                margin-left: var(--sidebar-width);
                max-width: calc(100% - var(--sidebar-width) - 300px);
            }
        }
        
        @media (max-width: 1200px) {
            .main-content {
                max-width: calc(100% - var(--sidebar-width));
                margin-right: 0;
            }
            
            .ads-sidebar {
                display: none;
            }
        }
        
        @media (max-width: 768px) {
            .sidebar {
                width: var(--sidebar-collapsed);
                padding-top: 60px;
            }
            
            .logo {
                margin-left: var(--sidebar-collapsed);
                font-size: 1.2rem;
            }
            
            .main-content {
                margin-left: var(--sidebar-collapsed);
                max-width: calc(100% - var(--sidebar-collapsed));
            }
            
            .ads-left-sidebar {
                display: none;
            }
            
            .sidebar-item {
                justify-content: center;
                padding: 1rem 0.5rem;
            }
            
            .sidebar-item .label {
                display: none;
            }
            
            .sidebar-item .icon {
                margin: 0;
            }
        }
        
        /* Navigation */
        .nav-links {
            display: flex;
            gap: 1.5rem;
            align-items: center;
        }
        
        .nav-links a {
            color: var(--gray-color);
            text-decoration: none;
            font-weight: 500;
            transition: var(--transition);
            position: relative;
        }
        
        .nav-links a:hover {
            color: var(--primary-color);
        }
        
        .nav-links a::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 0;
            height: 2px;
            background: var(--primary-color);
            transition: var(--transition);
        }
        
        .nav-links a:hover::after {
            width: 100%;
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
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.5s ease, transform 0.5s ease;
        }
        
        [data-bs-theme="dark"] .tool-container {
            background: var(--light-color);
        }
        
        .tool-container.active {
            display: block;
            opacity: 1;
            transform: translateY(0);
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
        
        .upload-text h4 {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--dark-color);
        }
        
        .upload-text p {
            color: var(--gray-color);
            margin-bottom: 0;
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
        
        /* Form Controls */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--dark-color);
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
        
        .btn-warning {
            background: var(--warning-color);
            color: white;
        }
        
        .btn-danger {
            background: var(--danger-color);
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
        
        .action-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            flex-wrap: wrap;
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
        
        @media (max-width: 1400px) {
            .footer-content {
                margin-left: var(--sidebar-width);
            }
        }
        
        @media (max-width: 768px) {
            .footer-content {
                margin-left: var(--sidebar-collapsed);
            }
        }
        
        .footer-logo {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.25rem;
            color: var(--primary-color);
            text-decoration: none;
        }
        
        .footer-info {
            color: var(--gray-color);
            font-size: 0.9rem;
            text-align: center;
        }
        
        .footer-info strong {
            color: var(--dark-color);
        }
        
        .footer-links {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
        }
        
        .footer-links a {
            color: var(--gray-color);
            text-decoration: none;
            transition: var(--transition);
        }
        
        .footer-links a:hover {
            color: var(--primary-color);
        }
        
        /* Ads Sidebar (Right) */
        .ads-sidebar {
            width: 300px;
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
        }
        
        [data-bs-theme="dark"] .ads-sidebar {
            background: rgba(26, 29, 32, 0.95);
            border-left: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .ad-sidebar-item {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--light-color);
            border-radius: var(--border-radius);
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
            backdrop-filter: blur(5px);
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
        
        /* Responsive */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2rem;
            }
            
            .hero-subtitle {
                font-size: 1rem;
            }
            
            .action-buttons {
                flex-direction: column;
            }
            
            .footer-content {
                flex-direction: column;
                text-align: center;
            }
            
            .nav-links {
                flex-wrap: wrap;
                justify-content: center;
                gap: 1rem;
            }
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
            background: var(--light-color);
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
            margin-left: 1rem;
        }
        
        @media (max-width: 768px) {
            .mobile-menu-toggle {
                display: block;
            }
            
            .sidebar {
                transform: translateX(-100%);
            }
            
            .sidebar.open {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
                max-width: 100%;
            }
            
            .logo {
                margin-left: 0;
            }
            
            .footer-content {
                margin-left: 0;
            }
            
            .ads-sidebar {
                display: none;
            }
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
            <div class="nav-links d-none d-md-flex">
                <a href="/mentions-legales">Mentions</a>
                <a href="/politique-confidentialite">Confidentialité</a>
                <a href="/conditions-utilisation">Conditions</a>
                <a href="/contact">Contact</a>
                <a href="/a-propos">À propos</a>
            </div>
            
            <button class="theme-toggle" id="themeToggle">
                <i class="fas fa-moon"></i>
            </button>
            
            <div class="dropdown d-md-none">
                <button class="btn btn-outline dropdown-toggle" type="button" data-bs-toggle="dropdown">
                    <i class="fas fa-bars"></i>
                </button>
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item" href="/mentions-legales">Mentions légales</a></li>
                    <li><a class="dropdown-item" href="/politique-confidentialite">Confidentialité</a></li>
                    <li><a class="dropdown-item" href="/conditions-utilisation">Conditions</a></li>
                    <li><a class="dropdown-item" href="/contact">Contact</a></li>
                    <li><a class="dropdown-item" href="/a-propos">À propos</a></li>
                </ul>
            </div>
        </div>
    </header>

    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h5 class="mb-0">Outils PDF</h5>
        </div>
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
        <!-- Publicité gauche sous les outils -->
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
        
        <!-- Widget d'outils rapides -->
        <div class="ad-sidebar-item">
            <h6 class="mb-3"><i class="fas fa-bolt me-2"></i>Outils Rapides</h6>
            <div class="small">
                <p class="mb-2">Fusionnez jusqu'à 10 PDFs en un clic</p>
                <p class="mb-2">Divisez par pages ou plages</p>
                <p class="mb-2">Tournez à 90°, 180° ou 270°</p>
                <p class="mb-0">Compressez sans perte de qualité</p>
            </div>
        </div>
        
        <!-- Deuxième pub verticale -->
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
        <div class="ad-sidebar-item">
            <h6 class="mb-3"><i class="fas fa-chart-bar me-2"></i>Statistiques</h6>
            <div class="small">
                <div class="d-flex justify-content-between mb-2">
                    <span>Opérations totales:</span>
                    <span id="totalOps">0</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span>Fusions:</span>
                    <span id="mergeCount">0</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span>Divisions:</span>
                    <span id="splitCount">0</span>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Rotations:</span>
                    <span id="rotateCount">0</span>
                </div>
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
            VERSION: "{{ config.VERSION }}",
            DEVELOPER_NAME: "{{ config.DEVELOPER_NAME }}",
            DEVELOPER_EMAIL: "{{ config.DEVELOPER_EMAIL }}",
            HOSTING: "{{ config.HOSTING }}",
            DOMAIN: "{{ config.DOMAIN }}"
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
            loaderOverlay: document.getElementById('loaderOverlay'),
            loaderMessage: document.getElementById('loaderMessage'),
            toastContainer: document.getElementById('toastContainer'),
            stats: {
                totalOps: document.getElementById('totalOps'),
                mergeCount: document.getElementById('mergeCount'),
                splitCount: document.getElementById('splitCount'),
                rotateCount: document.getElementById('rotateCount')
            }
        };

        // Initialize Application
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
            initSidebar();
            initFileUploads();
            initStats();
            loadStats();
            optimizeAds();
        });

        // Theme Management
        function initTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
            updateThemeIcon(savedTheme);
            
            elements.themeToggle.addEventListener('click', toggleTheme);
        }

        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        }

        function updateThemeIcon(theme) {
            elements.themeToggle.innerHTML = theme === 'light' 
                ? '<i class="fas fa-moon"></i>' 
                : '<i class="fas fa-sun"></i>';
        }

        // Sidebar Management
        function initSidebar() {
            elements.sidebarItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const tool = item.dataset.tool;
                    switchTool(tool);
                    
                    // Close mobile menu if open
                    if (window.innerWidth <= 768) {
                        elements.sidebar.classList.remove('open');
                    }
                });
            });

            // Mobile menu toggle
            elements.mobileMenuToggle.addEventListener('click', () => {
                elements.sidebar.classList.toggle('open');
            });

            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 768 && 
                    !elements.sidebar.contains(e.target) && 
                    !elements.mobileMenuToggle.contains(e.target)) {
                    elements.sidebar.classList.remove('open');
                }
            });
        }

        function switchTool(tool) {
            // Update active sidebar item
            elements.sidebarItems.forEach(item => {
                item.classList.toggle('active', item.dataset.tool === tool);
            });

            // Update active container
            elements.toolContainers.forEach(container => {
                container.classList.toggle('active', container.id === `${tool}Tool`);
            });

            state.activeTool = tool;
        }

        // File Upload Management
        function initFileUploads() {
            // Merge Tool
            initUploadZone('merge', true);
            // Split Tool
            initUploadZone('split', false);
            // Rotate Tool
            initUploadZone('rotate', false);
            // Compress Tool
            initUploadZone('compress', false);

            // Split mode change handler
            document.getElementById('splitMode').addEventListener('change', updateSplitMode);
        }

        function initUploadZone(tool, multiple) {
            const zone = document.getElementById(`${tool}UploadZone`);
            const input = document.getElementById(`${tool}FileInput`);
            
            if (!zone || !input) return;

            // Click handler
            zone.addEventListener('click', () => input.click());

            // File input change handler
            input.addEventListener('change', (e) => handleFileSelect(tool, e.target.files, multiple));

            // Drag and drop handlers
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.add('drag-over'), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.remove('drag-over'), false);
            });

            zone.addEventListener('drop', (e) => {
                handleFileSelect(tool, e.dataTransfer.files, multiple);
            }, false);
        }

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        function handleFileSelect(tool, files, multiple) {
            if (!files || files.length === 0) return;

            if (multiple) {
                // Add files to array
                const newFiles = Array.from(files).filter(file => 
                    file.type === 'application/pdf' && file.size <= 50 * 1024 * 1024
                );
                
                if (newFiles.length === 0) {
                    showToast('error', 'Format invalide', 'Seuls les fichiers PDF de moins de 50MB sont acceptés.');
                    return;
                }

                state.files[tool].push(...newFiles);
                if (state.files[tool].length > 10) {
                    state.files[tool] = state.files[tool].slice(0, 10);
                    showToast('warning', 'Limite atteinte', 'Maximum 10 fichiers autorisés.');
                }

                updateFileList(tool);
                updateMergeButton();
            } else {
                // Single file
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
            const container = document.getElementById(`${tool}FileList`);
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
            const container = document.getElementById(`${tool}FileInfo`);
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
                            <small>${formatFileSize(file.size)} • ${new Date(file.lastModified).toLocaleDateString()}</small>
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
            const button = document.getElementById(`${tool}Button`);
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
                    argInput.disabled = false;
                    break;
                case 'range':
                    argLabel.textContent = 'Plages de pages';
                    argInput.placeholder = 'Ex: 1-3, 5-7, 10-12';
                    helpText.textContent = 'Séparez les plages par des virgules (ex: 1-3,5-7)';
                    argInput.disabled = false;
                    break;
                case 'selected':
                    argLabel.textContent = 'Pages spécifiques';
                    argInput.placeholder = 'Ex: 1, 4, 8, 12';
                    helpText.textContent = 'Séparez les numéros de page par des virgules';
                    argInput.disabled = false;
                    break;
            }
        }

        // Stats Management
        function initStats() {
            // Load initial stats
            loadStats();
            
            // Refresh stats every 30 seconds
            setInterval(loadStats, 30000);
        }

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

            showLoader('Génération de l\\'aperçu...');

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
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la génération de l\\'aperçu');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de générer l\\'aperçu');
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
                    showToast('success', 'Succès', `${result.pages} pages fusionnées avec succès`);
                    loadStats(); // Refresh stats
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
                        // Download all files
                        result.files.forEach(file => {
                            downloadFile(file.data, file.filename, 'application/pdf');
                        });
                        showToast('success', 'Succès', `${result.count} fichiers générés avec succès`);
                        loadStats(); // Refresh stats
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

            showLoader('Création de l\\'archive ZIP...');

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
                    showToast('success', 'Succès', `Archive ZIP avec ${result.count} fichiers créée`);
                    loadStats(); // Refresh stats
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la création du ZIP');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de créer l\\'archive ZIP');
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
                    showToast('success', 'Succès', `${result.rotated} pages tournées sur ${result.pages} totales`);
                    loadStats(); // Refresh stats
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
                    showToast('success', 'Succès', `Fichier compressé avec ${result.pages} pages`);
                    loadStats(); // Refresh stats
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
        }

        function hideLoader() {
            elements.loaderOverlay.style.display = 'none';
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

        // Optimiser le chargement des publicités
        function optimizeAds() {
            // Attendre que le DOM soit chargé
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initAds);
            } else {
                initAds();
            }
        }

        function initAds() {
            // Charger les pubs avec un léger délai pour améliorer les performances
            setTimeout(() => {
                const ads = document.querySelectorAll('.adsbygoogle');
                ads.forEach(ad => {
                    try {
                        if (!ad.getAttribute('data-adsbygoogle-status')) {
                            (adsbygoogle = window.adsbygoogle || []).push({});
                        }
                    } catch (e) {
                        console.log('Erreur de chargement pub:', e);
                    }
                });
            }, 1000);
        }

        // Global functions for onclick handlers
        window.processMerge = processMerge;
        window.processSplit = processSplit;
        window.processSplitZip = processSplitZip;
        window.processRotate = processRotate;
        window.processCompress = processCompress;
        window.clearMergeFiles = clearMergeFiles;
        window.resetRotateForm = resetRotateForm;
        window.generatePreview = generatePreview;
        window.removeFile = removeFile;
        window.clearFile = clearFile;

    </script>
    {{ rating_html }}
</body>
</html>
"""

# ============================================================
# ROUTES
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
        datetime=datetime,  # AJOUTEZ CETTE LIGNE
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
        datetime=datetime,  # AJOUTEZ CETTE LIGNE
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
        datetime=datetime,  # AJOUTEZ CETTE LIGNE
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
        datetime=datetime,  # AJOUTEZ CETTE LIGNE
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
        datetime=datetime,  # AJOUTEZ CETTE LIGNE
        rating_html=get_rating_html()  # AJOUTEZ CETTE LIGNE
    )

# ============================================================
# API ENDPOINTS
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
        "user_sessions": stats.get("user_sessions", 0)
    })

def get_rating_html():
    """Retourne le HTML du système d'évaluation"""
    return '''
    <div id="ratingPopup" class="rating-popup" style="display: none;">
        <div class="rating-content">
            <button id="closeRating" class="rating-close">&times;</button>
            <h4><i class="fas fa-star me-2"></i>Évaluez votre expérience</h4>
            <p class="text-muted mb-3">Comment avez-vous trouvé PDF Fusion Pro ?</p>
            
            <div class="stars mb-3">
                <i class="fas fa-star star" data-value="1"></i>
                <i class="fas fa-star star" data-value="2"></i>
                <i class="fas fa-star star" data-value="3"></i>
                <i class="fas fa-star star" data-value="4"></i>
                <i class="fas fa-star star" data-value="5"></i>
            </div>
            
            <div class="rating-feedback" style="display: none;">
                <textarea id="feedbackText" class="form-control mb-2" 
                          placeholder="Vos suggestions (optionnel)" rows="2"></textarea>
                <button id="submitRating" class="btn btn-primary btn-sm">Envoyer</button>
            </div>
            
            <div class="text-muted small mt-2">
                <i class="fas fa-lock me-1"></i> Vos retours sont anonymes
            </div>
        </div>
    </div>
    
    <style>
    .rating-popup {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        z-index: 9999;
        width: 320px;
        max-width: 90%;
        border: 1px solid #e9ecef;
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
    
    [data-bs-theme="dark"] .rating-popup {
        background: #1a1d20;
        border-color: #444;
    }
    
    .rating-content {
        padding: 1.5rem;
        position: relative;
    }
    
    .rating-close {
        position: absolute;
        top: 10px;
        right: 10px;
        background: none;
        border: none;
        font-size: 1.5rem;
        color: #6c757d;
        cursor: pointer;
        line-height: 1;
    }
    
    .rating-close:hover {
        color: #dc3545;
    }
    
    .stars {
        font-size: 2rem;
        color: #dee2e6;
        cursor: pointer;
    }
    
    .star {
        margin-right: 5px;
        transition: all 0.2s ease;
    }
    
    .star:hover,
    .star.active {
        color: #ffc107;
        transform: scale(1.2);
    }
    
    .rating-trigger {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--primary-color);
        color: white;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(67, 97, 238, 0.3);
        z-index: 9998;
        transition: all 0.3s ease;
    }
    
    .rating-trigger:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(67, 97, 238, 0.4);
    }
    </style>
    
    <script>
    // Gestion de l'évaluation
    document.addEventListener("DOMContentLoaded", function() {
        const ratingPopup = document.getElementById("ratingPopup");
        const ratingTrigger = document.createElement("div");
        const stars = document.querySelectorAll(".star");
        const feedbackDiv = document.querySelector(".rating-feedback");
        const feedbackText = document.getElementById("feedbackText");
        const submitBtn = document.getElementById("submitRating");
        const closeBtn = document.getElementById("closeRating");
        
        // Créer le bouton déclencheur
        ratingTrigger.className = "rating-trigger";
        ratingTrigger.innerHTML = '<i class="fas fa-star"></i>';
        document.body.appendChild(ratingTrigger);
        
        let selectedRating = 0;
        let hasRated = localStorage.getItem("hasRated");
        
        // Afficher le popup après 30 secondes (si pas déjà évalué)
        if (!hasRated) {
            setTimeout(() => {
                showRatingPopup();
            }, 30000);
        }
        
        // Ouvrir popup au clic sur le bouton
        ratingTrigger.addEventListener("click", showRatingPopup);
        
        // Fermer popup
        closeBtn.addEventListener("click", hideRatingPopup);
        
        // Gestion des étoiles
        stars.forEach(star => {
            star.addEventListener("click", function() {
                const value = parseInt(this.dataset.value);
                selectedRating = value;
                
                // Mettre à jour l'affichage des étoiles
                stars.forEach((s, index) => {
                    if (index < value) {
                        s.classList.add("active");
                        s.style.color = "#ffc107";
                    } else {
                        s.classList.remove("active");
                        s.style.color = "#dee2e6";
                    }
                });
                
                // Afficher le champ de feedback
                feedbackDiv.style.display = "block";
                submitBtn.disabled = false;
            });
            
            star.addEventListener("mouseover", function() {
                const value = parseInt(this.dataset.value);
                stars.forEach((s, index) => {
                    s.style.color = index < value ? "#ffd700" : "#dee2e6";
                });
            });
            
            star.addEventListener("mouseout", function() {
                stars.forEach((s, index) => {
                    s.style.color = index < selectedRating ? "#ffc107" : "#dee2e6";
                });
            });
        });
        
        // Soumission
        submitBtn.addEventListener("click", function() {
            const feedback = feedbackText.value.trim();
            
            // Désactiver le bouton pendant l'envoi
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Envoi...';
            
            // Envoyer au serveur
            fetch("/api/rating", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    rating: selectedRating,
                    feedback: feedback,
                    page: window.location.pathname,
                    user_agent: navigator.userAgent
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remplacer le contenu par un message de remerciement
                    document.querySelector(".rating-content").innerHTML = `
                        <div class="text-center py-4">
                            <i class="fas fa-check-circle text-success" style="font-size: 3rem;"></i>
                            <h4 class="mt-3">Merci !</h4>
                            <p class="text-muted">Votre évaluation a été enregistrée.</p>
                            <p class="small text-muted">Note moyenne: ${data.average || "5.0"}/5</p>
                            <button class="btn btn-sm btn-outline-secondary mt-2" onclick="hideRatingPopup()">
                                Fermer
                            </button>
                        </div>
                    `;
                    
                    localStorage.setItem("hasRated", "true");
                    
                    // Cacher le bouton trigger après 5 secondes
                    setTimeout(() => {
                        if (ratingTrigger) {
                            ratingTrigger.style.display = "none";
                        }
                    }, 5000);
                } else {
                    // En cas d'erreur du serveur
                    alert("Erreur: " + (data.error || "Impossible d'enregistrer votre évaluation."));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = "Envoyer";
                }
            })
            .catch(error => {
                console.error("Erreur:", error);
                alert("Erreur de connexion. Veuillez réessayer.");
                submitBtn.disabled = false;
                submitBtn.innerHTML = "Envoyer";
            });
        });
        
        function showRatingPopup() {
            // Réinitialiser l'animation
            ratingPopup.style.opacity = "1";
            ratingPopup.style.transform = "translateY(0)";
            ratingPopup.style.display = "block";
            ratingTrigger.style.display = "none";
        }
        
        function hideRatingPopup() {
            ratingPopup.style.opacity = "0";
            ratingPopup.style.transform = "translateY(20px)";
            setTimeout(() => {
                ratingPopup.style.display = "none";
                ratingTrigger.style.display = "flex";
                // Réinitialiser les styles pour la prochaine fois
                setTimeout(() => {
                    ratingPopup.style.opacity = "1";
                    ratingPopup.style.transform = "translateY(0)";
                }, 10);
            }, 300);
        }
        
        // Exposer la fonction globalement pour le onclick
        window.hideRatingPopup = hideRatingPopup;
    });
    </script>
    '''
