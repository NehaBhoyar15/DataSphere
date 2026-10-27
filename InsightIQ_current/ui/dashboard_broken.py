
    def build_filters(self):
        panel = QFrame()
        panel.setObjectName("panel")

        row = QHBoxLayout(panel)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(10)

        filter_label = QLabel("FILTERS")
        filter_label.setStyleSheet(
            "font-size: 11px; font-weight: 800; color: #718096;"
        )

        self.period_filter = QComboBox()
        self.period_filter.addItems([
            "All Dates",
            "Last 30 Days",
            "Last 90 Days",
            "This Year",
        ])
        self.period_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.region_filter = QComboBox()
        self.region_filter.addItem("All Regions")
        self.region_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_data)

        row.addWidget(filter_label)
        row.addWidget(self.period_filter)
        row.addWidget(self.category_filter)
        row.addWidget(self.region_filter)
        row.addStretch()
        row.addWidget(refresh_button)

        self.layout.addWidget(panel)

        # User Profile
        self.user_profile = UserProfileCard(
            user_id="USR-001",
            username="Demo User",
            email="user@example.com",
        )

        self.user_profile.setVisible(True)

        self.user_profile.edit_requested.connect(
            self.edit_user_profile
        )

        self.layout.addWidget(self.user_profile)
        self.user_profile.raise_()
